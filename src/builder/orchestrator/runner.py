from typing import Dict, Optional, Union
from .backlog import BacklogTracker
from .state import OrchestratorState, TaskMetadata, TaskStatus
from .project_adapter import ProjectAdapter, ProjectConfig
from .failures import FailureClassifier
from .repair import RepairWorkflow
from .review import ReviewChecker
from .audit import log_selected_task, log_classification_result, log_review_verdict, log_repair_decision

class OrchestratorRunner:
    def __init__(self, config: Union[ProjectConfig, ProjectAdapter], backlog_tracker: BacklogTracker, initial_state: OrchestratorState):
        self.backlog_tracker = backlog_tracker
        self.state = initial_state
        self.config = config if isinstance(config, ProjectConfig) else config.config

    def load_project_config(self) -> None:
        pass

    def read_backlog(self) -> None:
        self.state = OrchestratorState(tasks=self.backlog_tracker.load_state(self.config.tasks_directory))

    def select_next_task(self) -> Optional[TaskMetadata]:
        tasks = self.backlog_tracker.scan_tasks()
        next_task = self.backlog_tracker.get_next_task(tasks)
        return next_task

    def run_review(self, task_name: str, changed_files: list) -> dict:
        review_checker = ReviewChecker(deliverables=[task_name], changed_files=changed_files)
        return review_checker.evaluate()

    def run_next_task(self, dry_run: bool = False) -> Dict[str, Union[str, bool]]:
        self.read_backlog()
        next_task = self.select_next_task()

        if next_task:
            if dry_run:
                return {
                    "dry_run": True,
                    "task_name": next_task.name,
                    "status": "planned",
                    "message": "Task is planned for execution."
                }
            else:
                next_task = TaskMetadata(name=next_task.name, order=next_task.order, status=TaskStatus(status="running"))
                execution_result = self.execute_task(next_task.name)  # Placeholder for actual execution logic
                return self.process_execution_result(execution_result, next_task.name)
        else:
            return {
                "dry_run": dry_run,
                "task_name": "none",
                "status": "no_task",
                "message": "No pending tasks available.",
                "outcome": "noop",
                "next_action": "none",
                "requires_approval": False
            }

    def execute_task(self, task_name: str) -> dict:
        # Simulated execution logic
        return {"success": True, "changed_files": ["file1.py"], "output": "Task executed successfully."}

    def process_execution_result(self, execution_result: dict, task_name: str) -> Dict[str, Union[str, bool]]:
        success = execution_result.get("success", False) or execution_result.get("status") == "success"
        changed_files = execution_result.get("changed_files", [])
        failure_text = execution_result.get("failure_text", "")
        message = execution_result.get("output", "")

        if success:
            log_selected_task(task_name, self.config.tasks_directory)
            review_result = self.run_review(task_name, changed_files)
            if review_result["mergeable"]:
                log_review_verdict("approved", self.config.tasks_directory)
                return {
                    "task_name": task_name,
                    "status": "running",
                    "message": "Task is now running.",
                    "outcome": "ready_for_pr",
                    "next_action": "merge",
                    "requires_approval": False
                }
            else:
                log_review_verdict("blocked", self.config.tasks_directory)
                return {
                    "task_name": task_name,
                    "status": "running",
                    "message": "Task is now running.",
                    "outcome": "review_blocked",
                    "next_action": "review",
                    "requires_approval": True
                }
        else:
            classifier = FailureClassifier()
            classification = classifier.classify(message, failure_text, changed_files)
            repair_workflow = RepairWorkflow(classification["category"], changed_files)
            repair_action = repair_workflow.determine_repair_action()
            log_classification_result(classification["category"], self.config.tasks_directory)
            log_repair_decision(repair_action["action"], self.config.tasks_directory)
            return {
                "task_name": task_name,
                "status": "failed",
                "message": f"Execution failed: {failure_text}",
                "outcome": repair_action["action"],
                "next_action": repair_action["recommended_action"],
                "requires_approval": repair_action["requires_approval"]
            }
