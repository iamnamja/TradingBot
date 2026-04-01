from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from agents.lib.task_queue import (
    BatchPostTaskDecision,
    QueueStatus,
    TaskQueueItem,
    decide_post_task_action,
    may_proceed_to_next_task,
)

BatchStatus = Literal["active", "completed", "blocked", "failed", "manual_patch"]
CheckpointTransition = Literal[
    "pending",
    "running",
    "completed_clean",
    "failed_requires_cleanup",
    "manual_patch_requires_isolation",
    "blocked_requires_manual",
]


class BatchStateError(ValueError):
    """Raised when batch state persistence or resume validation fails."""


@dataclass(frozen=True)
class BatchTaskCheckpoint:
    task_path: str
    ordinal: int
    context_kind: str
    context_ref: str
    completed_cleanly: bool
    cleanup_required_before_next_task: bool
    next_task_may_proceed: bool
    transition: CheckpointTransition
    note: str
    event_seq: int
    post_task_decision: BatchPostTaskDecision = "stop"

    def to_dict(self) -> dict[str, object]:
        return {
            "task_path": self.task_path,
            "ordinal": self.ordinal,
            "context_kind": self.context_kind,
            "context_ref": self.context_ref,
            "completed_cleanly": self.completed_cleanly,
            "cleanup_required_before_next_task": self.cleanup_required_before_next_task,
            "next_task_may_proceed": self.next_task_may_proceed,
            "transition": self.transition,
            "note": self.note,
            "event_seq": self.event_seq,
            "post_task_decision": self.post_task_decision,
        }


@dataclass(frozen=True)
class BatchTaskState:
    task_path: str
    ordinal: int
    status: QueueStatus
    status_note: str
    attempts: int
    updated_seq: int


@dataclass(frozen=True)
class BatchState:
    manifest_source: str
    manifest_fingerprint: str
    queue: tuple[BatchTaskState, ...]
    checkpoints: tuple[BatchTaskCheckpoint, ...]
    current_index: int
    state_version: int
    event_seq: int
    created_ts: int
    updated_ts: int
    batch_status: BatchStatus
    next_task_may_proceed: bool
    post_task_decision: BatchPostTaskDecision = "stop"

    def to_dict(self) -> dict[str, object]:
        return {
            "state_version": self.state_version,
            "manifest": {
                "source": self.manifest_source,
                "fingerprint": self.manifest_fingerprint,
            },
            "queue": [
                {
                    "task_path": item.task_path,
                    "ordinal": item.ordinal,
                    "status": item.status,
                    "status_note": item.status_note,
                    "attempts": item.attempts,
                    "updated_seq": item.updated_seq,
                }
                for item in self.queue
            ],
            "checkpoints": [checkpoint.to_dict() for checkpoint in self.checkpoints],
            "current_index": self.current_index,
            "event_seq": self.event_seq,
            "created_ts": self.created_ts,
            "updated_ts": self.updated_ts,
            "batch_status": self.batch_status,
            "next_task_may_proceed": self.next_task_may_proceed,
            "post_task_decision": self.post_task_decision,
        }


def manifest_fingerprint(manifest: dict[str, Any]) -> str:
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _queue_signature_from_items(items: list[TaskQueueItem]) -> tuple[str, ...]:
    return tuple(item.task_path for item in items)


def _queue_signature_from_state(state: BatchState) -> tuple[str, ...]:
    return tuple(item.task_path for item in state.queue)


def _derive_batch_status(queue: tuple[BatchTaskState, ...]) -> BatchStatus:
    statuses = [item.status for item in queue]
    if any(status == "running" for status in statuses):
        return "active"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "manual_patch" for status in statuses):
        return "manual_patch"
    if any(status == "failed" for status in statuses):
        return "failed"
    if statuses and all(status == "completed" for status in statuses):
        return "completed"
    return "active"


def _checkpoint_from_status(
    *,
    task_path: str,
    ordinal: int,
    status: QueueStatus,
    status_note: str,
    event_seq: int,
    decision: BatchPostTaskDecision,
) -> BatchTaskCheckpoint:
    if status == "completed":
        transition: CheckpointTransition = "completed_clean"
        completed_cleanly = True
        cleanup_required = False
    elif status == "manual_patch":
        transition = "manual_patch_requires_isolation"
        completed_cleanly = False
        cleanup_required = True
    elif status == "blocked":
        transition = "blocked_requires_manual"
        completed_cleanly = False
        cleanup_required = True
    elif status == "failed":
        transition = "failed_requires_cleanup"
        completed_cleanly = False
        cleanup_required = True
    elif status == "running":
        transition = "running"
        completed_cleanly = False
        cleanup_required = False
    else:
        transition = "pending"
        completed_cleanly = False
        cleanup_required = False

    return BatchTaskCheckpoint(
        task_path=task_path,
        ordinal=ordinal,
        context_kind="branch",
        context_ref="",
        completed_cleanly=completed_cleanly,
        cleanup_required_before_next_task=cleanup_required,
        next_task_may_proceed=decision == "continue",
        transition=transition,
        note=status_note,
        event_seq=event_seq,
        post_task_decision=decision,
    )


def create_batch_state(
    *,
    manifest: dict[str, Any],
    queue: list[TaskQueueItem],
    manifest_source: str = "",
    now_ts: int = 0,
) -> BatchState:
    queue_state = tuple(
        BatchTaskState(
            task_path=item.task_path,
            ordinal=item.ordinal,
            status=item.status,
            status_note=item.status_note,
            attempts=0,
            updated_seq=0,
        )
        for item in queue
    )
    initial_decision: BatchPostTaskDecision = "continue" if not queue_state else "stop"
    return BatchState(
        manifest_source=manifest_source,
        manifest_fingerprint=manifest_fingerprint(manifest),
        queue=queue_state,
        checkpoints=(),
        current_index=0,
        state_version=1,
        event_seq=0,
        created_ts=now_ts,
        updated_ts=now_ts,
        batch_status=_derive_batch_status(queue_state),
        next_task_may_proceed=not queue_state,
        post_task_decision=initial_decision,
    )


def apply_task_result(
    state: BatchState,
    *,
    ordinal: int,
    status: QueueStatus,
    status_note: str = "",
    now_ts: int | None = None,
    validator_ok: bool = True,
    deliverable_complete: bool = True,
    protected_lane_ok: bool = True,
    duplicate_bundle_conflict: bool = False,
    manual_patch_recommended: bool = False,
) -> BatchState:
    if ordinal < 1 or ordinal > len(state.queue):
        raise BatchStateError(f"Task ordinal out of range: {ordinal}")

    idx = ordinal - 1
    queue = list(state.queue)
    prev = queue[idx]
    queue[idx] = BatchTaskState(
        task_path=prev.task_path,
        ordinal=prev.ordinal,
        status=status,
        status_note=status_note,
        attempts=prev.attempts + 1,
        updated_seq=state.event_seq + 1,
    )

    decision = decide_post_task_action(
        status,
        signals={
            "validator_ok": validator_ok,
            "deliverable_complete": deliverable_complete,
            "protected_lane_ok": protected_lane_ok,
            "duplicate_bundle_conflict": duplicate_bundle_conflict,
            "manual_patch_recommended": manual_patch_recommended,
        },
    )
    may_proceed = decision == "continue" and may_proceed_to_next_task(status)

    checkpoints = list(state.checkpoints)
    checkpoints.append(
        _checkpoint_from_status(
            task_path=prev.task_path,
            ordinal=prev.ordinal,
            status=status,
            status_note=status_note,
            event_seq=state.event_seq + 1,
            decision=decision,
        )
    )

    current_index = idx + 1 if may_proceed else idx

    return BatchState(
        manifest_source=state.manifest_source,
        manifest_fingerprint=state.manifest_fingerprint,
        queue=tuple(queue),
        checkpoints=tuple(checkpoints),
        current_index=current_index,
        state_version=state.state_version,
        event_seq=state.event_seq + 1,
        created_ts=state.created_ts,
        updated_ts=state.updated_ts if now_ts is None else now_ts,
        batch_status=_derive_batch_status(tuple(queue)),
        next_task_may_proceed=may_proceed,
        post_task_decision=decision,
    )


def save_batch_state(path: str | Path, state: BatchState) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_batch_state(path: str | Path) -> BatchState:
    p = Path(path)
    if not p.exists():
        raise BatchStateError(f"Batch state file not found: {p.as_posix()}")
    payload = json.loads(p.read_text(encoding="utf-8"))

    queue = tuple(
        BatchTaskState(
            task_path=str(item.get("task_path", "")),
            ordinal=int(item.get("ordinal", 0)),
            status=str(item.get("status", "queued")),  # type: ignore[arg-type]
            status_note=str(item.get("status_note", "")),
            attempts=int(item.get("attempts", 0)),
            updated_seq=int(item.get("updated_seq", 0)),
        )
        for item in payload.get("queue", [])
    )

    checkpoints = tuple(
        BatchTaskCheckpoint(
            task_path=str(item.get("task_path", "")),
            ordinal=int(item.get("ordinal", 0)),
            context_kind=str(item.get("context_kind", "")),
            context_ref=str(item.get("context_ref", "")),
            completed_cleanly=bool(item.get("completed_cleanly", False)),
            cleanup_required_before_next_task=bool(
                item.get("cleanup_required_before_next_task", False)
            ),
            next_task_may_proceed=bool(item.get("next_task_may_proceed", False)),
            transition=str(item.get("transition", "pending")),  # type: ignore[arg-type]
            note=str(item.get("note", "")),
            event_seq=int(item.get("event_seq", 0)),
            post_task_decision=str(item.get("post_task_decision", "stop")),  # type: ignore[arg-type]
        )
        for item in payload.get("checkpoints", [])
    )

    manifest = payload.get("manifest", {})
    return BatchState(
        manifest_source=str(manifest.get("source", "")),
        manifest_fingerprint=str(manifest.get("fingerprint", "")),
        queue=queue,
        checkpoints=checkpoints,
        current_index=int(payload.get("current_index", 0)),
        state_version=int(payload.get("state_version", 1)),
        event_seq=int(payload.get("event_seq", 0)),
        created_ts=int(payload.get("created_ts", 0)),
        updated_ts=int(payload.get("updated_ts", 0)),
        batch_status=str(payload.get("batch_status", "active")),  # type: ignore[arg-type]
        next_task_may_proceed=bool(payload.get("next_task_may_proceed", False)),
        post_task_decision=str(payload.get("post_task_decision", "stop")),  # type: ignore[arg-type]
    )
