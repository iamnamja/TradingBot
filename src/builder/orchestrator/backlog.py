import json
import os
from typing import List, Optional

from .state import TaskMetadata, TaskStatus


class BacklogTracker:
    def __init__(self, tasks_directory: str):
        self.tasks_directory = tasks_directory

    @staticmethod
    def _is_task_file(filename: str) -> bool:
        """
        Valid task files look like:
        001_task_name.py
        001_task_name.md
        """
        if len(filename) < 5:
            return False

        if not filename[:3].isdigit():
            return False

        if filename[3] != "_":
            return False

        return filename.endswith(".md") or filename.endswith(".py")

    @staticmethod
    def _task_name_from_filename(filename: str) -> str:
        # Keep old behavior for tests: strip "001_" prefix from the stored task name
        return filename[4:]

    def scan_tasks(self) -> List[TaskMetadata]:
        tasks: List[TaskMetadata] = []

        for filename in os.listdir(self.tasks_directory):
            if not self._is_task_file(filename):
                continue

            order = int(filename[:3])
            name = self._task_name_from_filename(filename)

            tasks.append(
                TaskMetadata(
                    name=name,
                    order=order,
                    status=TaskStatus(status="pending"),
                )
            )

        return sorted(tasks, key=lambda task: task.order)

    def get_next_task(self, tasks: List[TaskMetadata]) -> Optional[TaskMetadata]:
        for task in tasks:
            if task.status.status == "pending":
                return task
        return None

    def load_state(self, state_file: str) -> List[TaskMetadata]:
        if os.path.exists(state_file):
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [
                    TaskMetadata(
                        name=task["name"],
                        order=task["order"],
                        status=TaskStatus(status=task["status"]),
                    )
                    for task in data["tasks"]
                ]
        return []

    def save_state(self, state_file: str, tasks: List[TaskMetadata]) -> None:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "tasks": [
                        {
                            "name": task.name,
                            "order": task.order,
                            "status": task.status.status,
                        }
                        for task in tasks
                    ]
                },
                f,
            )