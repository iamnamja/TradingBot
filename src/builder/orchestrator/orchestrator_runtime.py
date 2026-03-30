from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional

from .backlog_state import BacklogStateEngine, BacklogStatus, BacklogTaskState


@dataclass
class OrchestratorRuntimeState:
    backlog_state: BacklogStateEngine = field(default_factory=BacklogStateEngine)
    active_task_id: Optional[str] = None
    last_selected_task_id: Optional[str] = None
    remediation_context: Dict[str, str] = field(default_factory=dict)
    autonomy_context: Dict[str, str] = field(default_factory=dict)

    def register_task(self, task_id: str, *, status: BacklogStatus = BacklogStatus.READY) -> None:
        existing = self.backlog_state.get(task_id)
        metadata = dict(existing.metadata) if existing else {}
        self.backlog_state.upsert(
            BacklogTaskState(task_id=task_id, status=status, metadata=metadata)
        )

    def set_task_status(
        self,
        task_id: str,
        status: BacklogStatus,
        *,
        reason: Optional[str] = None,
        approval_ref: Optional[str] = None,
        manual_patch_note: Optional[str] = None,
    ) -> None:
        existing = self.backlog_state.get(task_id)
        metadata = dict(existing.metadata) if existing else {}
        self.backlog_state.upsert(
            BacklogTaskState(
                task_id=task_id,
                status=status,
                blocker_reason=reason if status == BacklogStatus.BLOCKED else None,
                waiting_approval_for=approval_ref if status == BacklogStatus.WAITING_APPROVAL else None,
                manual_patch_note=manual_patch_note if status == BacklogStatus.MANUAL_PATCH else None,
                deferred_reason=reason if status == BacklogStatus.DEFERRED else None,
                metadata=metadata,
            )
        )

    def pick_next_ready_task(self, ordered_task_ids: Iterable[str]) -> Optional[str]:
        task = self.backlog_state.next_ready_task(ordered_task_ids)
        if task is None:
            self.active_task_id = None
            return None
        self.active_task_id = task.task_id
        self.last_selected_task_id = task.task_id
        return task.task_id

    def remember_remediation_context(self, **context: str) -> None:
        self.remediation_context.update(context)

    def remember_autonomy_context(self, **context: str) -> None:
        self.autonomy_context.update(context)

    def to_dict(self) -> Dict[str, object]:
        return {
            "active_task_id": self.active_task_id,
            "last_selected_task_id": self.last_selected_task_id,
            "remediation_context": dict(self.remediation_context),
            "autonomy_context": dict(self.autonomy_context),
            "backlog_state": self.backlog_state.as_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "OrchestratorRuntimeState":
        backlog_raw = payload.get("backlog_state", {})
        backlog_state = (
            BacklogStateEngine.from_dict(backlog_raw)
            if isinstance(backlog_raw, dict)
            else BacklogStateEngine()
        )
        remediation = payload.get("remediation_context", {})
        autonomy = payload.get("autonomy_context", {})
        return cls(
            backlog_state=backlog_state,
            active_task_id=payload.get("active_task_id")
            if isinstance(payload.get("active_task_id"), str) or payload.get("active_task_id") is None
            else None,
            last_selected_task_id=payload.get("last_selected_task_id")
            if isinstance(payload.get("last_selected_task_id"), str)
            or payload.get("last_selected_task_id") is None
            else None,
            remediation_context=dict(remediation) if isinstance(remediation, dict) else {},
            autonomy_context=dict(autonomy) if isinstance(autonomy, dict) else {},
        )
