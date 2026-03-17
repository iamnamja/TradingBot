from pathlib import Path
from typing import Any, Dict, Optional, Union
import subprocess

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

    def load_project_config(self) -> None:
        pass

    def _state_file_path(self) -> str:
        return str(Path(self.config.tasks_directory) / "state.json")

    def read_backlog(self) -> None:
        state_file = self._state_file_path()
        self.state = OrchestratorState(tasks=self.backlog_tracker.load_state(state_file))

    def select_next_task(self) -> Optional[TaskMetadata]:
        tasks = self.backlog_tracker.scan_tasks()
        return self.backlog_tracker.get_next_task(tasks)

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

        running_task = TaskMetadata(
            name=next_task.name,
            order=next_task.order,
            status=TaskStatus(status="running"),
        )

        execution_result = self.execute_task(running_task)
        normalized_result = normalize_execution_result(execution_result)
        return self.process_execution_result(normalized_result, running_task)

    def execute_task(self, task: TaskMetadata) -> dict[str, Any]:
        task_runner_command = getattr(self.config, "task_runner_command", None)

        if task_runner_command:
            task_file_path = Path(self.config.tasks_directory) / task.name
            result = subprocess.run(
                [task_runner_command, str(task_file_path)],
                capture_output=True,
                text=True,
            )
            return {
                "success": result.returncode == 0,
                "status": "success" if result.returncode == 0 else "failure",
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
                "task_file": str(task_file_path),
            }

        return {
            "success": True,
            "output": "Task executed successfully",
            "changed_files": [],
        }

    def process_execution_result(
        self, execution_result: dict[str, Any], task: TaskMetadata
    ) -> dict[str, Any]:
        audit_path = getattr(self.config, "audit_log_path", None)

        log_selected_task(task.name, audit_path)

        success = execution_result.get("success", False)
        failure_text = execution_result.get("failure_text", "")
        changed_files = execution_result.get("changed_files", [])
        deliverables_updated = execution_result.get("deliverables_updated", [])

        if not success:
            classifier = FailureClassifier()
            classification_result = classifier.classify(
                runner_output=execution_result.get("output", ""),
                failure_text=failure_text,
                changed_files=changed_files,
            )

            log_classification_result(
                classification_result.get("category", "unknown"), audit_path
            )

            repair_workflow = RepairWorkflow(
                failure_classification=classification_result.get("category", "unknown"),
                changed_files=changed_files,
            )

            repair_action = repair_workflow.determine_repair_action()
            log_repair_decision(repair_action.get("action", "unknown"), audit_path)

            next_action = repair_action.get("action", "require_human_review")

            if repair_action.get("requires_approval", True):
                checkpoint = create_approval_checkpoint(
                    task_name=task.name,
                    reason=repair_action.get("reason", "Failure requires approval"),
                    source="repair_workflow",
                    requested_action=next_action,
                )
                log_approval_checkpoint(checkpoint, audit_path)

            return {
                "task_name": task.name,
                "status": "failed",
                "message": f"Execution failed: {failure_text}" if failure_text else "Execution failed.",
                "outcome": "repair_required",
                "next_action": next_action,
                "requires_approval": repair_action.get("requires_approval", True),
            }

        if changed_files and deliverables_updated is not None and len(deliverables_updated) == 0:
            return {
                "task_name": task.name,
                "status": "running",
                "message": "Task is now running.",
                "outcome": "review_blocked",
                "next_action": "requires_approval",
                "requires_approval": True,
            }

        review_result = self.run_review(changed_files)
        log_review_verdict(
            "mergeable" if review_result.get("mergeable", False) else "blocked",
            audit_path,
        )

        if not review_result.get("mergeable", False):
            checkpoint = create_approval_checkpoint(
                task_name=task.name,
                reason="Review blocked",
                source="review_checker",
                requested_action="requires_approval",
            )
            log_approval_checkpoint(checkpoint, audit_path)

            return {
                "task_name": task.name,
                "status": "running",
                "message": "Task is now running.",
                "outcome": "review_blocked",
                "next_action": "requires_approval",
                "requires_approval": True,
            }

        return {
            "task_name": task.name,
            "status": "running",
            "message": "Task is now running.",
            "outcome": "ready_for_pr",
            "next_action": "merge",
            "requires_approval": False,
        }

    def simulate_backlog(self) -> dict[str, Any]:
        tasks = self.backlog_tracker.scan_tasks()
        processed_tasks = []
        planned_actions = []
        stopped_reason = ""
        approval_required = False
        final_status = "completed"

        while True:
            next_task = self.backlog_tracker.get_next_task(tasks)
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

            tasks = [
                t
                if t.name != next_task.name
                else TaskMetadata(
                    name=t.name,
                    order=t.order,
                    status=TaskStatus(status="completed"),
                )
                for t in tasks
            ]

        return {
            "processed_tasks": processed_tasks,
            "planned_actions": planned_actions,
            "stopped_reason": stopped_reason,
            "approval_required": approval_required,
            "final_status": final_status,
        }
