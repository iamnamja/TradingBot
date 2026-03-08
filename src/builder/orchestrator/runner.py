from typing import Any, Dict, Optional, Union

from .audit import (
    log_classification_result,
    log_repair_decision,
    log_review_verdict,
    log_selected_task,
)
from .backlog import BacklogTracker
from .failures import FailureClassifier
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

    def read_backlog(self) -> None:
        self.state = OrchestratorState(
            tasks=self.backlog_tracker.load_state(self.config.tasks_directory)
        )

    def select_next_task(self) -> Optional[TaskMetadata]:
        tasks = self.backlog_tracker.scan_tasks()
        return self.backlog_tracker.get_next_task(tasks)

    def run_review(self, changed_files: list[str]) -> dict[str, Any]:
        effective_changed = list(changed_files or [])
        if not effective_changed:
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
        return self.process_execution_result(execution_result, running_task)

    def execute_task(self, task: TaskMetadata) -> dict[str, Any]:
        # Simulate task execution for the default happy path.
        return {
            "success": True,
            "output": "Task executed successfully",
            "changed_files": ["file1.py"],
        }

    def process_execution_result(
        self, execution_result: dict[str, Any], task: TaskMetadata
    ) -> Dict[str, Union[str, bool]]:
        success = (
            execution_result.get("success", False)
            if "success" in execution_result
            else execution_result.get("status") == "success"
        )
        output = execution_result.get("output", "")
        changed_files = execution_result.get("changed_files", [])
        failure_text = execution_result.get("failure_text", "")

        if success:
            log_selected_task(task.name, None)
            review_result = self.run_review(changed_files)
            if bool(review_result.get("mergeable", False)):
                log_review_verdict("approved", None)
                return {
                    "task_name": task.name,
                    "status": "running",
                    "message": "Task is now running.",
                    "outcome": "ready_for_pr",
                    "next_action": "merge",
                    "requires_approval": False,
                }

            log_review_verdict("blocked", None)
            return {
                "task_name": task.name,
                "status": "running",
                "message": "Task is now running.",
                "outcome": "review_blocked",
                "next_action": "requires_approval",
                "requires_approval": True,
            }

        classifier = FailureClassifier()
        classification_result = classifier.classify(output, failure_text, changed_files)
        repair_workflow = RepairWorkflow(classification_result["category"], changed_files)
        repair_action = repair_workflow.determine_repair_action()

        log_classification_result(classification_result["category"], None)
        log_repair_decision(repair_action.get("action", "repair_required"), None)

        next_action = (
            repair_action.get("recommended_action")
            or repair_action.get("next_action")
            or repair_action.get("action")
            or "require_human_review"
        )

        return {
            "task_name": task.name,
            "status": "failed",
            "message": f"Execution failed: {failure_text}" if failure_text else "Execution failed.",
            "outcome": "repair_required",
            "next_action": next_action,
            "requires_approval": True,
        }
