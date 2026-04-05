from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any, Literal

from agents.lib.controller_contract import (
    AcceptanceDecision,
    BatchPostTaskDecision,
    BatchStatus,
    ResumeMode,
    batch_status_for_post_task_decision,
    canonical_repair_audit,
    canonical_resume_metadata,
    coerce_non_negative_int,
)
from agents.lib.task_queue import QueueStatus, TaskQueueItem, validate_queue_status_transition

CheckpointTransition = Literal[
    "pending",
    "running",
    "completed_clean",
    "failed_requires_cleanup",
    "manual_patch_requires_isolation",
    "blocked_requires_manual",
]


class BatchStateError(ValueError):
    """Raised when persisted batch state is invalid or inconsistent."""


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
    post_task_decision: BatchPostTaskDecision | str = "stop"
    acceptance_decision: AcceptanceDecision | str = ""
    execution_attempt_count: int = 0
    repair_count: int = 0
    accepted_after_repair: bool = False
    retry_count: int = 0
    accepted_task_pr_flow_completed: bool | None = None
    required_checks_passed: bool | None = None
    merged_to_main: bool | None = None
    clean_main_reset_completed: bool | None = None

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
            "execution_attempt_count": self.execution_attempt_count,
            "repair_count": self.repair_count,
            "accepted_after_repair": self.accepted_after_repair,
            "retry_count": self.retry_count,
            "accepted_task_pr_flow_completed": self.accepted_task_pr_flow_completed,
            "required_checks_passed": self.required_checks_passed,
            "merged_to_main": self.merged_to_main,
            "clean_main_reset_completed": self.clean_main_reset_completed,
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
    post_task_decision: BatchPostTaskDecision | str = "stop"
    resume_reason: str = ""
    resume_target_task_path: str = ""
    resume_gate: str = ""

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



def last_checkpoint_for_task(state: BatchState, task_path: str) -> BatchTaskCheckpoint | None:
    for checkpoint in reversed(state.checkpoints):
        if checkpoint.task_path == task_path:
            return checkpoint
    return None



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
    queue_items = list(state.queue)
    queue_items[task_index] = updated_item
    queue_state = tuple(queue_items)

    next_index = state.current_index
    if to_status in {"completed", "failed", "manual_patch", "blocked"} and task_index >= next_index:
        next_index = task_index + 1

    return replace(
        state,
        queue=queue_state,
        current_index=next_index,
        event_seq=new_seq,
        updated_ts=event_ts or state.updated_ts,
        batch_status=_derive_batch_status(queue_state),
    )



def apply_task_result(
    state: BatchState,
    *,
    task_path: str,
    terminal_status: QueueStatus,
    post_task_decision: BatchPostTaskDecision | str,
    note: str,
    updated_ts: int | None = None,
    context_kind: str = "branch",
    context_ref: str = "",
    acceptance_decision: AcceptanceDecision | str = "",
    execution_attempt_count: int | None = None,
    repair_count: int = 0,
    accepted_after_repair: bool | None = None,
    retry_count: int | None = None,
    next_task_may_proceed: bool | None = None,
    accepted_task_pr_flow_completed: bool | None = None,
    required_checks_passed: bool | None = None,
    merged_to_main: bool | None = None,
    clean_main_reset_completed: bool | None = None,
) -> BatchState:
    if updated_ts is None:
        updated_ts = state.updated_ts + 1

    task_index = next((idx for idx, item in enumerate(state.queue) if item.task_path == task_path), None)
    if task_index is None:
        raise BatchStateError(f"Task path not found: {task_path}")

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
    if next_task_may_proceed is None:
        next_task_may_proceed = terminal_status == "completed"

    if terminal_status == "completed":
        transition: CheckpointTransition = "completed_clean"
    elif terminal_status == "manual_patch":
        transition = "manual_patch_requires_isolation"
    elif terminal_status == "blocked":
        transition = "blocked_requires_manual"
    else:
        transition = "failed_requires_cleanup"

    audit = canonical_repair_audit(
        execution_attempt_count=current.attempts if execution_attempt_count is None else execution_attempt_count,
        repair_count=repair_count if retry_count is None else retry_count,
        acceptance_decision=acceptance_decision,
        accepted_after_repair=accepted_after_repair,
    )

    checkpoint = BatchTaskCheckpoint(
        task_path=current.task_path,
        ordinal=current.ordinal,
        context_kind=context_kind,
        context_ref=context_ref,
        completed_cleanly=terminal_status == "completed",
        cleanup_required_before_next_task=terminal_status != "completed" or not bool(next_task_may_proceed),
        next_task_may_proceed=bool(next_task_may_proceed),
        transition=transition,
        note=note,
        event_seq=state.event_seq,
        post_task_decision=post_task_decision,
        acceptance_decision=acceptance_decision,
        execution_attempt_count=coerce_non_negative_int(audit["execution_attempt_count"]),
        repair_count=coerce_non_negative_int(audit["repair_count"]),
        accepted_after_repair=bool(audit["accepted_after_repair"]),
        retry_count=coerce_non_negative_int(audit["retry_count"]),
        accepted_task_pr_flow_completed=accepted_task_pr_flow_completed,
        required_checks_passed=required_checks_passed,
        merged_to_main=merged_to_main,
        clean_main_reset_completed=clean_main_reset_completed,
    )

    batch_status = batch_status_for_post_task_decision(
        default_status=_derive_batch_status(state.queue),
        post_task_decision=post_task_decision,
    )

    return replace(
        state,
        checkpoints=state.checkpoints + (checkpoint,),
        next_task_may_proceed=bool(next_task_may_proceed),
        post_task_decision=post_task_decision,
        batch_status=batch_status,
        updated_ts=updated_ts,
    )



def mark_resume_plan(
    state: BatchState,
    *,
    queue: list[TaskQueueItem],
    resume_mode: ResumeMode,
    resume_target_task_path: str | None,
    explicit_resume: bool,
    updated_ts: int,
) -> BatchState:
    del queue  # queue is present for API symmetry / future validation.
    metadata = canonical_resume_metadata(
        resume_mode=resume_mode,
        resume_target_task_path=resume_target_task_path,
        explicit_resume=explicit_resume,
    )
    return replace(
        state,
        resume_reason=metadata["resume_reason"],
        resume_target_task_path=metadata["resume_target_task_path"],
        resume_gate=metadata["resume_gate"],
        updated_ts=updated_ts,
    )



def record_resume_skip(
    state: BatchState,
    *,
    task_path: str,
    reason: str,
    updated_ts: int,
) -> BatchState:
    task_index = next((idx for idx, item in enumerate(state.queue) if item.task_path == task_path), None)
    if task_index is None:
        return state
    next_index = max(state.current_index, task_index + 1)
    return replace(
        state,
        current_index=next_index,
        resume_reason=reason,
        updated_ts=updated_ts,
    )
