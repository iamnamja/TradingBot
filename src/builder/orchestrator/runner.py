from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import subprocess

from .backlog import BacklogTracker
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

        return {"success": True, "changed_files": []}

    def process_execution_result(
        self, execution_result: dict[str, Any], task: TaskMetadata
    ) -> dict[str, Union[str, bool]]:
        success = execution_result.get("success", False)

        if not success:
            failure_text = (
                execution_result.get("failure_text")
                or execution_result.get("stderr")
                or ""
            )
            message = f"Execution failed: {failure_text}" if failure_text else "Execution failed."
            return {
                "task_name": task.name,
                "status": "failed",
                "message": message,
                "outcome": "repair_required",
                "next_action": "require_human_review",
                "requires_approval": True,
            }

        changed_files = execution_result.get("changed_files", [])
        review_result = self.run_review(changed_files)
        mergeable = review_result.get("mergeable", True)
        requires_approval = not mergeable

        if requires_approval:
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

    def simulate_backlog(self) -> Dict[str, Any]:
        processed_tasks: List[str] = []
        planned_actions: List[str] = []
        stopped_reason = ""
        final_status = "completed"
        approval_required = False

        while True:
            next_task = self.backlog_tracker.get_next_task([])
            if not next_task:
                break

            processed_tasks.append(next_task.name)
            execution_result = self.execute_task(next_task)
            result = self.process_execution_result(execution_result, next_task)

            if result["status"] == "failed":
                stopped_reason = execution_result.get("failure_text", "Execution failed")
                final_status = "failed"
                approval_required = False
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
