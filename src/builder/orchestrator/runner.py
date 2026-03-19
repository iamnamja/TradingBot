from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Union

from .backlog import BacklogTracker
from .execution_result import normalize_execution_result
from .git_guardrails import GitGuardrails
from .policy import PolicyEngine
from .project_adapter import ProjectAdapter, ProjectConfig
from .review import ReviewChecker
from .state import OrchestratorState, TaskMetadata, TaskStatus


class OrchestratorRunner:
    def __init__(
        self,
        config: Union[ProjectConfig, ProjectAdapter],
        backlog_tracker: BacklogTracker,
        initial_state: OrchestratorState,
    ):
        self.backlog_tracker = backlog_tracker
        self.state = initial_state
        self.config = config if isinstance(config, ProjectConfig) else config.config
        self.skip_guardrails = False

        # Auto-load persisted state if available and no initial state provided
        try:
            state_path = self._state_file_path()
            if not self.state.tasks and Path(state_path).exists():
                self.state = OrchestratorState.load(state_path)  # type: ignore[attr-defined]
        except Exception:
            # If load fails, proceed with provided initial_state
            pass

    def load_project_config(self) -> None:
        # Backward-compat hook — no-op for now
        return

    def _state_file_path(self) -> str:
        configured_state_path = getattr(self.config, "state_path", None)
        if configured_state_path:
            return str(configured_state_path)
        return str(Path(self.config.tasks_directory) / "state.json")

    def _with_task_status(self, task: TaskMetadata, status: str) -> TaskMetadata:
        return TaskMetadata(
            name=task.name,
            order=task.order,
            status=TaskStatus(status=status),
        )

    def _replace_task_in_state(self, updated_task: TaskMetadata) -> None:
        replaced = False
        updated_tasks: List[TaskMetadata] = []
        for t in self.state.tasks:
            if t.name == updated_task.name and t.order == updated_task.order:
                updated_tasks.append(updated_task)
                replaced = True
            else:
                updated_tasks.append(t)
        if not replaced:
            updated_tasks.append(updated_task)
        self.state.tasks = updated_tasks

    def _overlay_state_on_scanned(self, scanned: List[TaskMetadata]) -> List[TaskMetadata]:
        """Overlay persisted statuses onto freshly scanned tasks."""
        state_index: Dict[tuple[int, str], str] = {
            (t.order, t.name): t.status.status for t in self.state.tasks
        }
        result: List[TaskMetadata] = []
        for t in scanned:
            key = (t.order, t.name)
            if key in state_index:
                result.append(self._with_task_status(t, state_index[key]))
            else:
                result.append(t)
        return result

    def select_next_task(self) -> TaskMetadata:
        tasks = self.backlog_tracker.scan_tasks()
        tasks = self._overlay_state_on_scanned(tasks)
        next_task = self.backlog_tracker.get_next_task(tasks)
        if next_task is None:
            # Return a sentinel TaskMetadata for "none"
            return TaskMetadata(name="none", order=0, status=TaskStatus(status="no_task"))
        return next_task

    def run_review(self, changed_files: List[str]) -> Dict[str, Any]:
        # Legacy/mock success path: if nothing changed, allow merge.
        if not changed_files:
            return {"mergeable": True}

        # Default permissive behavior (detailed compliance is handled when explicit
        # deliverables are provided to process_execution_result via ReviewChecker)
        return {"mergeable": True}

    def run_next_task(self, dry_run: bool = False) -> Dict[str, Any]:
        # Handle dry-run early
        if dry_run:
            tasks = self.backlog_tracker.scan_tasks()
            tasks = self._overlay_state_on_scanned(tasks)
            next_task = self.backlog_tracker.get_next_task(tasks)
            if not next_task:
                return {
                    "dry_run": True,
                    "task_name": "none",
                    "status": "no_task",
                    "message": "No pending tasks available.",
                    "outcome": "noop",
                    "next_action": "none",
                    "requires_approval": False,
                }
            return {
                "dry_run": True,
                "task_name": next_task.name,
                "status": "planned",
                "message": "Task is planned for execution.",
                "outcome": "noop",
                "next_action": "none",
                "requires_approval": False,
            }

        # Guardrails (only when a real command is configured and not skipped)
        if getattr(self.config, "task_runner_command", None) and not self.skip_guardrails:
            guardrails = GitGuardrails(branch_naming_pattern=self.config.branch_naming_pattern)
            safe, reason = guardrails.check()
            if not safe:
                return {
                    "task_name": "none",
                    "status": "blocked",
                    "message": f"Guardrails blocked execution: {reason}",
                    "outcome": "guardrail_failed",
                    "next_action": "none",
                    "requires_approval": False,
                }

        # Select next pending task (with state overlay)
        tasks = self.backlog_tracker.scan_tasks()
        tasks = self._overlay_state_on_scanned(tasks)
        next_task = self.backlog_tracker.get_next_task(tasks)
        if not next_task:
            return {
                "task_name": "none",
                "status": "no_task",
                "message": "No pending tasks available.",
                "outcome": "noop",
                "next_action": "none",
                "requires_approval": False,
            }

        # Mark as running in state and persist
        running_task = self._with_task_status(next_task, "running")
        self._replace_task_in_state(running_task)
        try:
            OrchestratorState.save(self.state, self._state_file_path())
        except Exception:
            pass

        # Execute task
        raw_execution = self.execute_task(next_task)
        normalized = normalize_execution_result(raw_execution)
        processed = self.process_execution_result(normalized, next_task)

        # Compose orchestrator result
        if processed.get("status") == "failed":
            # Persist failed state
            failed_task = self._with_task_status(next_task, "failed")
            self._replace_task_in_state(failed_task)
            try:
                OrchestratorState.save(self.state, self._state_file_path())
            except Exception:
                pass
            return {
                "task_name": next_task.name,
                "status": "failed",
                "message": f"Execution failed: {normalized.get('failure_text', 'Execution failed') or 'Execution failed'}",
                "outcome": "repair_required",
                "next_action": "require_human_review",
                "requires_approval": True,
            }

        # If approval is required (blocked)
        if processed.get("requires_approval"):
            blocked_task = self._with_task_status(next_task, "blocked")
            self._replace_task_in_state(blocked_task)
            try:
                OrchestratorState.save(self.state, self._state_file_path())
            except Exception:
                pass
            return {
                "task_name": next_task.name,
                "status": "running",
                "message": "Task is now running.",
                "outcome": "review_blocked",
                "next_action": "requires_approval",
                "requires_approval": True,
            }

        # Success path: mark completed
        completed_task = self._with_task_status(next_task, "completed")
        self._replace_task_in_state(completed_task)
        try:
            OrchestratorState.save(self.state, self._state_file_path())
        except Exception:
            pass

        return {
            "task_name": next_task.name,
            "status": "running",
            "message": "Task is now running.",
            "outcome": "ready_for_pr",
            "next_action": "merge",
            "requires_approval": False,
        }

    def execute_task(self, task: TaskMetadata) -> Dict[str, Any]:
        """
        Execute a task.

        Returns raw execution result; normalization is handled by normalize_execution_result.
        """
        command = getattr(self.config, "task_runner_command", None)
        # Build task file path. If task.name is already "001_task.py", use as-is.
        filename = task.name
        if not (len(filename) > 4 and filename[:3].isdigit() and filename[3] == "_"):
            filename = f"{task.order:03d}_{task.name}"
        task_path = str(Path(self.config.tasks_directory) / filename)

        if not command:
            # Default mock success path
            return {
                "success": True,
                "status": "success",
                "stdout": "",
                "stderr": "",
                "returncode": 0,
                "changed_files": [],
                "task_file": task_path,
            }

        try:
            result = subprocess.run(
                [command, task_path],
                capture_output=True,
                text=True,
                check=False,
            )
            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()
            success = result.returncode == 0
            return {
                "success": success,
                "status": "success" if success else "failure",
                "stdout": stdout,
                "stderr": stderr,
                "returncode": result.returncode,
                "changed_files": [],  # unknown in real execution by default
                "task_file": task_path,
                "failure_text": stderr if not success else "",
            }
        except Exception as exc:
            return {
                "success": False,
                "status": "failure",
                "stdout": "",
                "stderr": str(exc),
                "returncode": 1,
                "changed_files": [],
                "task_file": task_path,
                "failure_text": str(exc),
            }

    def process_execution_result(self, execution_result: Dict[str, Any], task: TaskMetadata) -> Dict[str, Any]:
        """
        Post-process a normalized execution result to determine orchestrator actions.
        """
        # Execution failed: classify and require human review
        if not execution_result.get("success", False):
            return {
                "status": "failed",
                "outcome": "repair_required",
                "next_action": "require_human_review",
                "requires_approval": True,
            }

        changed_files: List[str] = list(execution_result.get("changed_files", []) or [])

        # Initial verdict via pluggable run_review (supports test overrides)
        review_verdict = self.run_review(changed_files)
        mergeable = bool(review_verdict.get("mergeable", True))

        # If explicit deliverables are provided AND there are actual changes,
        # enforce stricter compliance using ReviewChecker.
        deliverables_updated: List[str] = list(execution_result.get("deliverables_updated", []) or [])
        if changed_files:
            checker = ReviewChecker(deliverables=deliverables_updated, changed_files=changed_files)
            scope_verdict = checker.evaluate()
            if not scope_verdict.get("mergeable", True):
                mergeable = False

        # Approval policy gate
        approval_engine = PolicyEngine(
            approval_required_file_patterns=getattr(self.config, "approval_required_file_patterns", []),
            protected_file_patterns=getattr(self.config, "protected_file_patterns", []),
        )
        requires_approval = approval_engine.requires_approval(changed_files)

        if not mergeable or requires_approval:
            return {
                "status": "running",
                "outcome": "review_blocked",
                "next_action": "requires_approval",
                "requires_approval": True,
            }

        # Ready for PR
        return {
            "status": "running",
            "outcome": "ready_for_pr",
            "next_action": "merge",
            "requires_approval": False,
        }

    def simulate_backlog(self) -> dict[str, Any]:
        processed_tasks: list[str] = []
        planned_actions: list[str] = []
        stopped_reason = ""
        approval_required = False
        final_status = "completed"

        while True:
            next_task = self.backlog_tracker.get_next_task([])
            if not next_task:
                break

            processed_tasks.append(next_task.name)
            execution_result = self.execute_task(next_task)
            normalized_result = normalize_execution_result(execution_result)
            result = self.process_execution_result(normalized_result, next_task)

            if result["status"] == "failed":
                stopped_reason = normalized_result.get("failure_text", "Execution failed")
                final_status = "failed"
                break

            if result.get("requires_approval", False):
                approval_required = True
                stopped_reason = "Approval required"
                final_status = "blocked"
                continue

            planned_actions.append(f"Task {next_task.name} completed successfully.")

        return {
            "processed_tasks": processed_tasks,
            "stopped_reason": stopped_reason,
            "final_status": final_status,
            "approval_required": approval_required,
            "planned_actions": planned_actions,
        }

    def run_loop(self, max_tasks: int = 100) -> dict[str, Any]:
        """
        Run tasks continuously until stop condition.
        Returns summary dict with processed_tasks, final_status, stopped_reason,
        approval_required, planned_actions.
        """
        processed_tasks: List[str] = []
        planned_actions: List[str] = []
        approval_required = False
        final_status = "completed"
        stopped_reason = ""

        audit_path = getattr(self.config, "audit_path", None)

        def _log_decision(task_name: str, outcome: str, iteration: int) -> None:
            if not audit_path:
                return
            try:
                entry = {
                    "task_name": task_name,
                    "outcome": outcome,
                    "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "iteration": iteration,
                }
                path = Path(audit_path)  # type: ignore[arg-type]
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception:
                # Silent on logging failures
                pass

        iteration = 0
        while iteration < max_tasks:
            iteration += 1
            result = self.run_next_task()
            task_name = result.get("task_name", "none")
            status = result.get("status", "")
            outcome = result.get("outcome", "")
            next_action = result.get("next_action", "")

            # Stop if no task available
            if status == "no_task" or task_name == "none":
                stopped_reason = "No pending tasks"
                final_status = "completed"
                # Do not print or log for the sentinel iteration
                break

            # Print iteration line
            print(f"[Task {iteration}] {task_name} — {outcome} ({next_action})")

            # Decision logging
            _log_decision(task_name, outcome, iteration)

            processed_tasks.append(task_name)
            planned_actions.append(f"{task_name}:{outcome}")

            # Stop conditions
            if status == "failed":
                final_status = "failed"
                stopped_reason = "Task failed"
                break

            if result.get("requires_approval", False):
                approval_required = True
                final_status = "blocked"
                stopped_reason = "Approval required"
                break

        else:
            # Max tasks reached
            final_status = "incomplete"
            stopped_reason = "Max tasks reached"

        return {
            "processed_tasks": processed_tasks,
            "stopped_reason": stopped_reason,
            "final_status": final_status,
            "approval_required": approval_required,
            "planned_actions": planned_actions,
        }
