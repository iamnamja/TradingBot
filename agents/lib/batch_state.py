from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any, Literal

from agents.lib.task_queue import BatchPostTaskDecision, QueueStatus, TaskQueueItem, validate_queue_status_transition

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
    acceptance_decision: str = ""
    retry_count: int = 0

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
            "acceptance_decision": self.acceptance_decision,
            "retry_count": self.retry_count,
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


def initialize_batch_state(
    *,
    manifest: dict[str, Any],
    queue: list[TaskQueueItem],
    manifest_source: str,
    created_ts: int,
) -> BatchState:
    queue_state = tuple(
        BatchTaskState(
            task_path=item.task_path,
            ordinal=item.ordinal,
            status="queued",
            status_note="",
            attempts=0,
            updated_seq=0,
        )
        for item in queue
    )
    return BatchState(
        manifest_source=manifest_source,
        manifest_fingerprint=manifest_fingerprint(manifest),
        queue=queue_state,
        checkpoints=(),
        current_index=0,
        state_version=1,
        event_seq=0,
        created_ts=created_ts,
        updated_ts=created_ts,
        batch_status="active",
        next_task_may_proceed=True,
        post_task_decision="continue",
    )


def advance_task_status(
    state: BatchState,
    *,
    task_index: int,
    to_status: QueueStatus,
    status_note: str = "",
    event_ts: int = 0,
) -> BatchState:
    if task_index < 0 or task_index >= len(state.queue):
        raise BatchStateError(f"Task index out of range: {task_index}")

    current = state.queue[task_index]
    validate_queue_status_transition(current.status, to_status)

    new_seq = state.event_seq + 1
    updated_item = replace(
        current,
        status=to_status,
        status_note=status_note,
        attempts=current.attempts + (1 if to_status == "running" else 0),
        updated_seq=new_seq,
    )

    queue_list = list(state.queue)
    queue_list[task_index] = updated_item
    queue_tuple = tuple(queue_list)

    next_index = state.current_index
    if to_status in {"completed", "failed", "manual_patch", "blocked"} and task_index >= next_index:
        next_index = task_index + 1

    return replace(
        state,
        queue=queue_tuple,
        current_index=next_index,
        event_seq=new_seq,
        updated_ts=event_ts or state.updated_ts,
        batch_status=_derive_batch_status(queue_tuple),
    )


def apply_task_result(
    state: BatchState,
    *,
    task_path: str,
    terminal_status: QueueStatus,
    post_task_decision: BatchPostTaskDecision,
    note: str,
    updated_ts: int,
    context_kind: str,
    context_ref: str,
    acceptance_decision: str = "",
    retry_count: int = 0,
    next_task_may_proceed: bool | None = None,
) -> BatchState:
    task_index = next((idx for idx, item in enumerate(state.queue) if item.task_path == task_path), None)
    if task_index is None:
        raise BatchStateError(f"Task path not found in queue: {task_path}")

    if state.queue[task_index].status != "running":
        state = advance_task_status(
            state,
            task_index=task_index,
            to_status="running",
            status_note="running",
            event_ts=updated_ts,
        )

    state = advance_task_status(
        state,
        task_index=task_index,
        to_status=terminal_status,
        status_note=note,
        event_ts=updated_ts,
    )

    current = state.queue[task_index]
    completed_cleanly = terminal_status == "completed"
    cleanup_required = terminal_status in {"failed", "manual_patch", "blocked"}

    if next_task_may_proceed is None:
        next_task_may_proceed = terminal_status == "completed"

    transition: CheckpointTransition
    if terminal_status == "completed":
        transition = "completed_clean"
    elif terminal_status == "manual_patch":
        transition = "manual_patch_requires_isolation"
    elif terminal_status == "blocked":
        transition = "blocked_requires_manual"
    else:
        transition = "failed_requires_cleanup"

    checkpoint = BatchTaskCheckpoint(
        task_path=current.task_path,
        ordinal=current.ordinal,
        context_kind=context_kind,
        context_ref=context_ref,
        completed_cleanly=completed_cleanly,
        cleanup_required_before_next_task=cleanup_required,
        next_task_may_proceed=bool(next_task_may_proceed),
        transition=transition,
        note=note,
        event_seq=state.event_seq,
        post_task_decision=post_task_decision,
        acceptance_decision=acceptance_decision,
        retry_count=int(retry_count),
    )

    return replace(
        state,
        checkpoints=state.checkpoints + (checkpoint,),
        next_task_may_proceed=bool(next_task_may_proceed),
        post_task_decision=post_task_decision,
    )
