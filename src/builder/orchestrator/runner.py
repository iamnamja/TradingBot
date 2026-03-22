from __future__ import annotations

import fnmatch
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .approval import create_approval_checkpoint
from .audit import (
    log_approval_checkpoint,
    log_classification_result,
    log_repair_decision,
    log_review_verdict,
    log_selected_task,
)
from .backlog import BacklogTracker
from .execution_result import normalize_execution_result
from .failures import FailureClassifier
from .git_guardrails import GitGuardrails
from .policy import PolicyEngine
from .project_adapter import ProjectAdapter, ProjectConfig
from .repair import RepairWorkflow
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

    def load_project_config(self) -> None:
        pass

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

        for existing_task in self.state.tasks:
            if (
                existing_task.order == updated_task.order
                and existing_task.name == updated_task.name
            ):
                updated_tasks.append(updated_task)
                replaced = True
            else:
                updated_tasks.append(existing_task)

        if not replaced:
            updated_tasks.append(updated_task)
            updated_tasks.sort(key=lambda task: task.order)

        self.state = OrchestratorState(tasks=updated_tasks)

    def write_state(self) -> None:
        self.backlog_tracker.save_state(self._state_file_path(), self.state.tasks)

    def read_backlog(self) -> None:
        state_file = self._state_file_path()
        scanned_tasks = self.backlog_tracker.scan_tasks()
        persisted_tasks = self.backlog_tracker.load_state(state_file)

        persisted_lookup = {(task.order, task.name): task for task in persisted_tasks}

        merged_tasks: List[TaskMetadata] = []
        for task in scanned_tasks:
            merged_tasks.append(persisted_lookup.get((task.order, task.name), task))

        self.state = OrchestratorState(tasks=merged_tasks)

    def select_next_task(self) -> Optional[TaskMetadata]:
        return self.backlog_tracker.get_next_task(self.state.tasks)

    def _sort_tasks(self, tasks: list[TaskMetadata]) -> list[TaskMetadata]:
        return sorted(tasks, key=lambda task: (getattr(task, "order", 0), getattr(task, "name", "")))

    def _task_class(self, task: TaskMetadata) -> str:
        raw = getattr(task, "task_class", None) or getattr(task, "task_type", None) or "default"
        return str(raw).strip().lower()

    def _task_file_paths(self, task: TaskMetadata) -> set[str]:
        raw_paths = (
            getattr(task, "changed_files", None)
            or getattr(task, "deliverables", None)
            or getattr(task, "file_paths", None)
            or getattr(task, "protected_files", None)
            or []
        )
        paths: set[str] = set()
        for path in raw_paths:
            text = str(path).replace("\\", "/").strip()
            if text:
                paths.add(text)
        return paths

    def _task_shared_state_keys(self, task: TaskMetadata) -> set[str]:
        raw_keys = (
            getattr(task, "shared_state_keys", None)
            or getattr(task, "shared_state", None)
            or getattr(task, "state_keys", None)
            or []
        )
        keys: set[str] = set()
        for key in raw_keys:
            text = str(key).strip()
            if text:
                keys.add(text)
        return keys

    def _policy_sensitive_patterns(self) -> list[str]:
        protected = list(getattr(self.config, "protected_file_patterns", []) or [])
        approval = list(getattr(self.config, "approval_required_file_patterns", []) or [])
        return protected + approval

    def _matches_any_policy_pattern(self, path: str, patterns: list[str]) -> bool:
        normalized = path.replace("\\", "/")
        return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)

    def _task_touches_policy_sensitive_surface(self, task: TaskMetadata) -> bool:
        patterns = self._policy_sensitive_patterns()
        if not patterns:
            return False
        return any(self._matches_any_policy_pattern(path, patterns) for path in self._task_file_paths(task))

    def _task_parallel_eligible(self, task: TaskMetadata) -> bool:
        if not bool(getattr(self.config, "parallel_execution_enabled", False)):
            return False
        if self._task_class(task) not in {"independent_safe", "parallel_safe"}:
            return False
        if self._task_touches_policy_sensitive_surface(task):
            return False
        return True

    def build_safe_parallel_groups(self, tasks: list[TaskMetadata]) -> list[list[TaskMetadata]]:
        ordered = self._sort_tasks(list(tasks))
        if not bool(getattr(self.config, "parallel_execution_enabled", False)):
            return [[task] for task in ordered]

        groups: list[list[TaskMetadata]] = []
        active_group: list[TaskMetadata] = []
        active_paths: set[str] = set()
        active_shared_state: set[str] = set()

        def flush_active_group() -> None:
            nonlocal active_group, active_paths, active_shared_state
            if active_group:
                groups.append(active_group)
            active_group = []
            active_paths = set()
            active_shared_state = set()

        for task in ordered:
            if not self._task_parallel_eligible(task):
                flush_active_group()
                groups.append([task])
                continue

            task_paths = self._task_file_paths(task)
            task_shared_state = self._task_shared_state_keys(task)
            overlaps_files = bool(active_paths & task_paths)
            overlaps_state = bool(active_shared_state & task_shared_state)

            if active_group and (overlaps_files or overlaps_state):
                flush_active_group()

            active_group.append(task)
            active_paths.update(task_paths)
            active_shared_state.update(task_shared_state)

        flush_active_group()
        return groups

    def execute_parallel_groups(
        self,
        groups: list[list[TaskMetadata]],
        executor: Any | None = None,
        *,
        max_workers: int | None = None,
    ) -> list[dict[str, Any]]:
        task_executor = executor or self.execute_task
        ordered_groups = sorted(
            list(groups),
            key=lambda group: min((getattr(task, "order", 0) for task in group), default=0),
        )

        results: list[dict[str, Any]] = []
        for group in ordered_groups:
            ordered_group = self._sort_tasks(list(group))
            if len(ordered_group) <= 1:
                for task in ordered_group:
                    results.append(task_executor(task))
                continue

            worker_count = max_workers or len(ordered_group)
            worker_count = max(1, min(worker_count, len(ordered_group)))

            with ThreadPoolExecutor(max_workers=worker_count) as pool:
                future_to_task = {pool.submit(task_executor, task): task for task in ordered_group}
                group_results: list[tuple[int, dict[str, Any]]] = []
                for future, task in future_to_task.items():
                    group_results.append((getattr(task, "order", 0), future.result()))
            group_results.sort(key=lambda item: item[0])
            results.extend(result for _, result in group_results)

        return results

    def run_safe_parallel_batch(
        self,
        tasks: list[TaskMetadata],
        executor: Any | None = None,
        *,
        max_workers: int | None = None,
    ) -> list[dict[str, Any]]:
        groups = self.build_safe_parallel_groups(tasks)
        return self.execute_parallel_groups(groups, executor=executor, max_workers=max_workers)

    def run_review(self, changed_files: list[str]) -> dict[str, Any]:
        effective_changed = list(changed_files or [])

        if not effective_changed:
            return {"mergeable": True}

        approval_patterns = getattr(self.config, "approval_required_file_patterns", [])
        policy = PolicyEngine(
            approval_required_file_patterns=approval_patterns,
            protected_file_patterns=getattr(self.config, "protected_file_patterns", []),
        )
        if policy.requires_approval(effective_changed):
            return {"mergeable": False}

        checker = ReviewChecker(
            deliverables=effective_changed,
            changed_files=effective_changed,
        )

        result = checker.evaluate()

        if "mergeable" not in result:
            return {"mergeable": True}

        return result

    def run_next_task(self, dry_run: bool = False) -> Dict[str, Union[str, bool]]:
        self.read_backlog()
        next_task = self.select_next_task()

        if not next_task:
            return {
                "dry_run": dry_run,
                "task_name": "none",
                "status": "no_task",
                "message": "No pending tasks available.",
                "outcome": "noop",
                "next_action": "none",
                "requires_approval": False,
            }

        if dry_run:
            return {
                "dry_run": True,
                "task_name": next_task.name,
                "status": "planned",
                "message": "Task is planned for execution.",
                "outcome": "noop",
                "next_action": "none",
                "requires_approval": False,
            }

        task_runner_command = getattr(self.config, "task_runner_command", None)
        skip_guardrails = getattr(self, "skip_guardrails", False)

        if task_runner_command and not skip_guardrails:
            branch_pattern = getattr(self.config, "branch_naming_pattern", "feature/*")
            guardrails = GitGuardrails(branch_naming_pattern=branch_pattern)
            safe, reason = guardrails.check()

            if not safe:
                return {
                    "task_name": "none",
                    "status": "blocked",
                    "message": f"Git guardrail failed: {reason}",
                    "outcome": "guardrail_failed",
                    "next_action": "fix_git_state",
                    "requires_approval": False,
                }

        running_task = self._with_task_status(next_task, "running")
        self._replace_task_in_state(running_task)

        log_selected_task(running_task.name, getattr(self.config, "audit_path", None))

        execution_result = self.execute_task(running_task)
        normalized_result = normalize_execution_result(execution_result)
        return self.process_execution_result(normalized_result, running_task)

    def execute_task(self, task: TaskMetadata) -> Dict[str, Any]:
        task_runner_command = getattr(self.config, "task_runner_command", None)

        if not task_runner_command:
            return {
                "success": True,
                "output": "Task executed successfully",
                "changed_files": [],
            }

        task_file = Path(self.config.tasks_directory) / task.name

        try:
            result = subprocess.run(
                [task_runner_command, str(task_file)],
                capture_output=True,
                text=True,
                timeout=300,
            )

            return {
                "success": result.returncode == 0,
                "status": "success" if result.returncode == 0 else "failure",
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
                "task_file": str(task_file),
                "changed_files": [],
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "status": "failure",
                "stdout": "",
                "stderr": "Task execution timed out",
                "returncode": 124,
                "task_file": str(task_file),
                "changed_files": [],
            }
        except Exception as exc:
            return {
                "success": False,
                "status": "failure",
                "stdout": "",
                "stderr": str(exc),
                "returncode": 1,
                "task_file": str(task_file),
                "changed_files": [],
            }

    def process_execution_result(
        self, execution_result: Dict[str, Any], task: TaskMetadata
    ) -> Dict[str, Any]:
        success = (
            execution_result.get("success", False)
            if "success" in execution_result
            else execution_result.get("status") == "success"
        )

        if not success:
            failure_text = (
                execution_result.get("failure_text", "")
                or execution_result.get("stderr", "")
            )

            classifier = FailureClassifier()
            classification = classifier.classify(
                execution_result.get("output", ""),
                failure_text,
                execution_result.get("changed_files", []),
            )

            log_classification_result(
                classification["category"], getattr(self.config, "audit_path", None)
            )

            repair_workflow = RepairWorkflow(
                classification["category"],
                execution_result.get("changed_files", []),
            )
            repair_action = repair_workflow.determine_repair_action()

            log_repair_decision(
                repair_action.get("action", "repair_required"),
                getattr(self.config, "audit_path", None),
            )

            next_action = (
                repair_action.get("recommended_action")
                or repair_action.get("next_action")
                or repair_action.get("action")
                or "require_human_review"
            )

            failed_task = self._with_task_status(task, "failed")
            self._replace_task_in_state(failed_task)
            self.write_state()

            return {
                "task_name": task.name,
                "status": "failed",
                "message": (
                    f"Execution failed: {failure_text}"
                    if failure_text
                    else "Execution failed."
                ),
                "outcome": "repair_required",
                "next_action": next_action,
                "requires_approval": repair_action.get("requires_approval", True),
            }

        changed_files = execution_result.get("changed_files", [])
        deliverables_updated = execution_result.get("deliverables_updated", [])

        if (
            changed_files
            and "deliverables_updated" in execution_result
            and len(deliverables_updated) == 0
        ):
            log_review_verdict("blocked", getattr(self.config, "audit_path", None))
            checkpoint = create_approval_checkpoint(
                task_name=task.name,
                reason="no_deliverables_updated",
                source="review_gate",
                requested_action="requires_approval",
            )
            checkpoint["status"] = "pending_approval"
            log_approval_checkpoint(checkpoint, getattr(self.config, "audit_path", None))

            blocked_task = self._with_task_status(task, "blocked")
            self._replace_task_in_state(blocked_task)
            self.write_state()

            return {
                "task_name": task.name,
                "status": "running",
                "message": "Task is now running.",
                "outcome": "review_blocked",
                "next_action": "requires_approval",
                "requires_approval": True,
            }

        review_result = self.run_review(changed_files)

        if not review_result.get("mergeable", False):
            log_review_verdict("blocked", getattr(self.config, "audit_path", None))
            checkpoint = create_approval_checkpoint(
                task_name=task.name,
                reason="review_blocked",
                source="merge_gate",
                requested_action="requires_approval",
            )
            checkpoint["status"] = "pending_approval"
            log_approval_checkpoint(checkpoint, getattr(self.config, "audit_path", None))

            blocked_task = self._with_task_status(task, "blocked")
            self._replace_task_in_state(blocked_task)
            self.write_state()

            return {
                "task_name": task.name,
                "status": "running",
                "message": "Task is now running.",
                "outcome": "review_blocked",
                "next_action": "requires_approval",
                "requires_approval": True,
            }

        log_review_verdict("approved", getattr(self.config, "audit_path", None))

        completed_task = self._with_task_status(task, "completed")
        self._replace_task_in_state(completed_task)
        self.write_state()

        return {
            "task_name": task.name,
            "status": "running",
            "message": "Task is now running.",
            "outcome": "ready_for_pr",
            "next_action": "merge",
            "requires_approval": False,
        }

    def run_loop(self, max_tasks: int = 100) -> dict[str, Any]:
        processed_tasks: List[str] = []
        planned_actions: List[str] = []
        approval_required = False
        stopped_reason = ""
        final_status = "completed"

        for _ in range(max_tasks):
            result = self.run_next_task()

            task_name = result.get("task_name", "none")
            if task_name == "none":
                stopped_reason = "No pending tasks available."
                final_status = "completed"
                break

            status = result.get("status", "")
            if status == "failed":
                processed_tasks.append(task_name)
                stopped_reason = result.get("message", "Execution failed.")
                final_status = "failed"
                break

            processed_tasks.append(task_name)
            planned_actions.append(f"Task {task_name} completed successfully.")

            if result.get("requires_approval", False):
                approval_required = True
                stopped_reason = "Approval required"
                final_status = "blocked"
                break

        else:
            stopped_reason = f"Reached max_tasks limit of {max_tasks}"
            final_status = "running" if processed_tasks else "completed"

        return {
            "processed_tasks": processed_tasks,
            "stopped_reason": stopped_reason,
            "final_status": final_status,
            "approval_required": approval_required,
            "planned_actions": planned_actions,
        }

    def simulate_backlog(self) -> Dict[str, Union[List[str], str, bool]]:
        processed_tasks: List[str] = []
        approval_required = False
        stopped_reason = ""
        final_status = "completed"
        planned_actions: List[str] = []

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
