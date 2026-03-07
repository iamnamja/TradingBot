from typing import Dict, Optional, Union
from .backlog import BacklogTracker
from .state import OrchestratorState, TaskMetadata, TaskStatus
from .project_adapter import ProjectAdapter, ProjectConfig

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
                return {
                    "task_name": next_task.name,
                    "status": "running",
                    "message": "Task is now running."
                }
        else:
            return {
                "dry_run": dry_run,
                "task_name": "none",
                "status": "no_task",
                "message": "No pending tasks available."
            }
