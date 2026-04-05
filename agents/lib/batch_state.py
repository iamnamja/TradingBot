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
ResumeMode = Literal["default", "resume_same_task", "resume_next", "resume_after_merge", "resume_after_manual_resolution"]
ResumeReason = Literal["none", "resume_same_task", "resume_next", "skip_accepted_merged", "resume_after_manual_resolution"]


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
    resume_reason: ResumeReason = "none"
    resume_target_task_path: str = ""
    resume_gate: str = "none"

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
            "resume_reason": self.resume_reason,
            "resume_target_task_path": self.resume_target_task_path,
            "resume_gate": self.resume_gate,
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
            status=item.status,
            status_note=item.status_note,
            attempts=0,
            updated_seq=0,
        )
        for item in queue
    )
    return BatchState(
        manifest_source=manifest_source,
        manifest_fingerprint=manifest_fingerprint(manifest),
        queue=queue_state,
        checkpoints=tuple(),
        current_index=0,
        state_version=1,
        event_seq=0,
        created_ts=created_ts,
        updated_ts=created_ts,
        batch_status=_derive_batch_status(queue_state),
        next_task_may_proceed=True,
        post_task_decision="stop",
    )


def last_checkpoint_for_task(state: BatchState, task_path: str) -> BatchTaskCheckpoint | None:
    for checkpoint in reversed(state.checkpoints):
        if checkpoint.task_path == task_path:
            return checkpoint
    return None


def _queue_index_for_path(state: BatchState, task_path: str) -> int:
    for idx, item in enumerate(state.queue):
        if item.task_path == task_path:
            return idx
    raise BatchStateError(f"Task path not found in batch state queue: {task_path}")


def _terminal_transition_for_status(status: QueueStatus) -> CheckpointTransition:
    if status == "completed":
        return "completed_clean"
    if status == "manual_patch":
        return "manual_patch_requires_isolation"
    if status == "blocked":
        return "blocked_requires_manual"
    return "failed_requires_cleanup"


def _advance_index_after_result(queue: tuple[BatchTaskState, ...], current_index: int, task_index: int) -> int:
    if task_index < current_index:
        return current_index
    if task_index != current_index:
        return current_index
    return min(len(queue), current_index + 1)


def advance_task_status(
    state: BatchState,
    *,
    task_index: int,
    to_status: QueueStatus,
    status_note: str,
    event_ts: int,
) -> BatchState:
    if task_index < 0 or task_index >= len(state.queue):
        raise BatchStateError(f"Task index out of range: {task_index}")

    current = state.queue[task_index]
    validate_queue_status_transition(current.status, to_status)

    next_event_seq = state.event_seq + 1
    updated = replace(
        current,
        status=to_status,
        status_note=status_note,
        attempts=current.attempts + (1 if to_status == "running" else 0),
        updated_seq=next_event_seq,
    )
    queue = list(state.queue)
    queue[task_index] = updated
    queue_tuple = tuple(queue)

    return replace(
        state,
        queue=queue_tuple,
        event_seq=next_event_seq,
        updated_ts=event_ts,
        batch_status=_derive_batch_status(queue_tuple),
        next_task_may_proceed=False,
        post_task_decision="stop",
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
    acceptance_decision: str,
    retry_count: int,
    next_task_may_proceed: bool,
) -> BatchState:
    task_index = _queue_index_for_path(state, task_path)
    current = state.queue[task_index]

    from_status = current.status
    if from_status != "running":
        validate_queue_status_transition("running", terminal_status)
    else:
        validate_queue_status_transition(from_status, terminal_status)

    next_event_seq = state.event_seq + 1
    updated_task = replace(
        current,
        status=terminal_status,
        status_note=note,
        updated_seq=next_event_seq,
    )
    queue = list(state.queue)
    queue[task_index] = updated_task
    queue_tuple = tuple(queue)

    checkpoint = BatchTaskCheckpoint(
        task_path=task_path,
        ordinal=updated_task.ordinal,
        context_kind=context_kind,
        context_ref=context_ref,
        completed_cleanly=terminal_status == "completed",
        cleanup_required_before_next_task=terminal_status != "completed",
        next_task_may_proceed=bool(next_task_may_proceed),
        transition=_terminal_transition_for_status(terminal_status),
        note=note,
        event_seq=next_event_seq,
        post_task_decision=post_task_decision,
        acceptance_decision=acceptance_decision,
        retry_count=int(retry_count),
    )

    return replace(
        state,
        queue=queue_tuple,
        checkpoints=state.checkpoints + (checkpoint,),
        current_index=_advance_index_after_result(queue_tuple, state.current_index, task_index),
        event_seq=next_event_seq,
        updated_ts=updated_ts,
        batch_status=_derive_batch_status(queue_tuple),
        next_task_may_proceed=bool(next_task_may_proceed),
        post_task_decision=post_task_decision,
    )


def _queued_after_index(queue: tuple[BatchTaskState, ...], start: int) -> BatchTaskState | None:
    for idx in range(max(0, start), len(queue)):
        item = queue[idx]
        if item.status == "queued":
            return item
    return None


def mark_resume_plan(
    state: BatchState,
    *,
    queue: list[TaskQueueItem],
    resume_mode: ResumeMode,
    resume_target_task_path: str | None,
    explicit_resume: bool,
    updated_ts: int,
) -> BatchState:
    del queue
    if resume_mode in {"resume_after_manual_resolution", "resume_same_task", "resume_next"} and not explicit_resume:
        raise BatchStateError("Blocked/manual resume requires explicit operator intent.")

    target = (resume_target_task_path or "").strip()
    resume_reason: ResumeReason = "none"
    resume_gate = "none"

    if resume_mode == "resume_after_merge":
        next_item = _queued_after_index(state.queue, state.current_index)
        resume_reason = "skip_accepted_merged"
        target = next_item.task_path if next_item is not None else ""
        resume_gate = "continue_from_next_pending"
    elif resume_mode == "resume_after_manual_resolution":
        if not target:
            raise BatchStateError("resume_after_manual_resolution requires resume_target_task_path.")
        idx = _queue_index_for_path(state, target)
        current = state.queue[idx]
        if current.status not in {"manual_patch", "blocked"}:
            raise BatchStateError("resume_after_manual_resolution target is not in manual_patch/blocked status.")
        resume_reason = "resume_after_manual_resolution"
        resume_gate = "explicit_manual_resolution"
    elif resume_mode == "resume_same_task":
        if not target:
            raise BatchStateError("resume_same_task requires resume_target_task_path.")
        resume_reason = "resume_same_task"
        resume_gate = "explicit_resume_same_task"
    elif resume_mode == "resume_next":
        next_item = _queued_after_index(state.queue, state.current_index)
        resume_reason = "resume_next"
        target = next_item.task_path if next_item is not None else target
        resume_gate = "explicit_resume_next"

    return replace(
        state,
        updated_ts=updated_ts,
        resume_reason=resume_reason,
        resume_target_task_path=target,
        resume_gate=resume_gate,
    )


def record_resume_skip(
    state: BatchState,
    *,
    task_path: str,
    reason: ResumeReason,
    updated_ts: int,
) -> BatchState:
    idx = _queue_index_for_path(state, task_path)
    next_index = max(state.current_index, idx + 1)
    target = ""
    next_item = _queued_after_index(state.queue, next_index)
    if next_item is not None:
        target = next_item.task_path

    return replace(
        state,
        current_index=next_index,
        updated_ts=updated_ts,
        resume_reason=reason,
        resume_target_task_path=target,
        resume_gate="continue_from_next_pending",
        post_task_decision="continue",
        next_task_may_proceed=True,
    )
