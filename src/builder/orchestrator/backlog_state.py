from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, Optional


class BacklogStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"
    WAITING_APPROVAL = "waiting_approval"
    MANUAL_PATCH = "manual_patch"
    COMPLETED = "completed"
    DEFERRED = "deferred"


@dataclass(frozen=True)
class BacklogTaskState:
    task_id: str
    status: BacklogStatus = BacklogStatus.READY
    blocker_reason: Optional[str] = None
    waiting_approval_for: Optional[str] = None
    manual_patch_note: Optional[str] = None
    deferred_reason: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def is_ready(self) -> bool:
        return self.status == BacklogStatus.READY


@dataclass
class BacklogStateEngine:
    tasks: Dict[str, BacklogTaskState] = field(default_factory=dict)
    _selection_cursor: int = 0

    def upsert(self, task_state: BacklogTaskState) -> None:
        self.tasks[task_state.task_id] = task_state

    def get(self, task_id: str) -> Optional[BacklogTaskState]:
        return self.tasks.get(task_id)

    def next_ready_task(self, ordered_task_ids: Iterable[str]) -> Optional[BacklogTaskState]:
        task_ids = list(ordered_task_ids)
        if not task_ids:
            return None
        start = self._selection_cursor % len(task_ids)
        for offset in range(len(task_ids)):
            idx = (start + offset) % len(task_ids)
            task_id = task_ids[idx]
            state = self.tasks.get(task_id)
            if state is not None and state.is_ready():
                self._selection_cursor = idx + 1
                return state
        return None

    def mark_completed(self, task_id: str) -> None:
        existing = self.tasks.get(task_id)
        metadata = dict(existing.metadata) if existing else {}
        self.tasks[task_id] = BacklogTaskState(
            task_id=task_id,
            status=BacklogStatus.COMPLETED,
            metadata=metadata,
        )

    def as_dict(self) -> Dict[str, dict]:
        return {
            task_id: {
                "task_id": state.task_id,
                "status": state.status.value,
                "blocker_reason": state.blocker_reason,
                "waiting_approval_for": state.waiting_approval_for,
                "manual_patch_note": state.manual_patch_note,
                "deferred_reason": state.deferred_reason,
                "metadata": dict(state.metadata),
            }
            for task_id, state in self.tasks.items()
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, dict]) -> "BacklogStateEngine":
        engine = cls()
        for task_id, raw in payload.items():
            engine.upsert(
                BacklogTaskState(
                    task_id=task_id,
                    status=BacklogStatus(raw.get("status", BacklogStatus.READY.value)),
                    blocker_reason=raw.get("blocker_reason"),
                    waiting_approval_for=raw.get("waiting_approval_for"),
                    manual_patch_note=raw.get("manual_patch_note"),
                    deferred_reason=raw.get("deferred_reason"),
                    metadata=dict(raw.get("metadata", {})),
                )
            )
        return engine
