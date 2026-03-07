from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class TaskStatus:
    status: str  # e.g., "pending", "running", "succeeded", "failed", "merged", "blocked", "skipped"

@dataclass(frozen=True)
class TaskMetadata:
    name: str
    order: int
    status: TaskStatus

@dataclass(frozen=True)
class OrchestratorState:
    tasks: List[TaskMetadata]
