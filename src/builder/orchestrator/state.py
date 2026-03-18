from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List


@dataclass
class TaskStatus:
    status: str  # e.g., "pending", "running", "succeeded", "failed", "merged", "blocked", "skipped"

    def to_dict(self) -> str:
        return self.status

    @classmethod
    def from_dict(cls, value: Any) -> "TaskStatus":
        return cls(status=str(value))


@dataclass
class TaskMetadata:
    name: str
    order: int
    status: TaskStatus

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "order": self.order,
            "status": self.status.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskMetadata":
        return cls(
            name=str(data["name"]),
            order=int(data["order"]),
            status=TaskStatus.from_dict(data["status"]),
        )


@dataclass
class OrchestratorState:
    tasks: List[TaskMetadata] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"tasks": [task.to_dict() for task in self.tasks]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrchestratorState":
        raw_tasks = data.get("tasks", []) if isinstance(data, dict) else []
        return cls(tasks=[TaskMetadata.from_dict(task) for task in raw_tasks])

    def save(self, state_path: str) -> None:
        path = Path(state_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def load(cls, state_path: str) -> "OrchestratorState":
        path = Path(state_path)
        if not path.exists():
            return cls(tasks=[])
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
