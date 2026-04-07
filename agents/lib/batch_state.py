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
    canonical_merge_posture_truth,
    canonical_resume_metadata,
    checkpoint_allows_resume_after_merge,
    checkpoint_requires_manual_resolution,
)
from agents.lib.git_workflow import canonical_required_check_truth
from agents.lib.multi_agent_contract import canonical_role_handoff_state, resume_role_handoff_state
from agents.lib.manifest_planner import plan_manifest_progress
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
    terminal_status: QueueStatus
    completed_cleanly: bool
    cleanup_required_before_next_task: bool
    next_task_may_proceed: bool
    transition: CheckpointTransition
    note: str
    event_seq: int
    post_task_decision: BatchPostTaskDecision | str = "stop"
    acceptance_decision: AcceptanceDecision | str = ""
    retry_count: int = 0
    accepted_task_pr_flow_completed: bool = False
    required_checks_passed: bool = False
    merged_to_main: bool = False
    clean_main_reset_completed: bool = False
    verification_authority_profile: str = "local_only"
    required_checks_configured: bool = False
    required_checks_discovered: bool = False
    required_checks_missing: bool = False
    required_checks_pending: bool = False
    required_checks_timed_out: bool = False
    required_checks_failed: bool = False
    missing_required_checks_blocks_merge: bool = False
    verification_authority_satisfied: bool = True
    hosted_checks_source: str = "not_required"
    hosted_checks_reported: bool = False
    hosted_authority_available: bool = True
    hosted_authority_satisfied: bool = True
    hosted_checks_source: str = ""
    hosted_checks_reported: bool = False
    hosted_authority_available: bool = True
    hosted_authority_satisfied: bool = True
    active_role: str = "controller"
    prior_role: str = ""
    role_attempt_count: int = 0
    handoff_reason: str = ""
    handoff_summary: str = ""
    handoff_instructions: str = ""
    role_output_summary: str = ""
    verifier_verdict: str = "not_run"
    controller_next_role_decision: str = "builder"
    role_outcome: str = "not_run"
    planner_selected_task_path: str = ""
    planner_reordered: bool = False
    planner_ready_task_paths: tuple[str, ...] = ()
    planner_blocked_task_paths: tuple[str, ...] = ()
    planner_deferred_task_paths: tuple[str, ...] = ()
    planner_skipped_task_paths: tuple[str, ...] = ()
    planner_rerun_required_task_paths: tuple[str, ...] = ()
    planner_blocking_reasons: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "task_path": self.task_path,
            "ordinal": self.ordinal,
            "context_kind": self.context_kind,
            "context_ref": self.context_ref,
            "terminal_status": self.terminal_status,
            "completed_cleanly": self.completed_cleanly,
            "cleanup_required_before_next_task": self.cleanup_required_before_next_task,
            "next_task_may_proceed": self.next_task_may_proceed,
            "transition": self.transition,
            "note": self.note,
            "event_seq": self.event_seq,
            "post_task_decision": self.post_task_decision,
            "acceptance_decision": self.acceptance_decision,
            "retry_count": self.retry_count,
            "accepted_task_pr_flow_completed": self.accepted_task_pr_flow_completed,
            "required_checks_passed": self.required_checks_passed,
            "merged_to_main": self.merged_to_main,
            "clean_main_reset_completed": self.clean_main_reset_completed,
            "verification_authority_profile": self.verification_authority_profile,
            "required_checks_configured": self.required_checks_configured,
            "required_checks_discovered": self.required_checks_discovered,
            "required_checks_missing": self.required_checks_missing,
            "required_checks_pending": self.required_checks_pending,
            "required_checks_timed_out": self.required_checks_timed_out,
            "required_checks_failed": self.required_checks_failed,
            "missing_required_checks_blocks_merge": self.missing_required_checks_blocks_merge,
            "verification_authority_satisfied": self.verification_authority_satisfied,
            "hosted_checks_source": self.hosted_checks_source,
            "hosted_checks_reported": self.hosted_checks_reported,
            "hosted_authority_available": self.hosted_authority_available,
            "hosted_authority_satisfied": self.hosted_authority_satisfied,
            "active_role": self.active_role,
            "prior_role": self.prior_role,
            "role_attempt_count": self.role_attempt_count,
            "handoff_reason": self.handoff_reason,
            "handoff_summary": self.handoff_summary,
            "handoff_instructions": self.handoff_instructions,
            "role_output_summary": self.role_output_summary,
            "verifier_verdict": self.verifier_verdict,
            "controller_next_role_decision": self.controller_next_role_decision,
            "role_outcome": self.role_outcome,
            "planner_selected_task_path": self.planner_selected_task_path,
            "planner_reordered": self.planner_reordered,
            "planner_ready_task_paths": list(self.planner_ready_task_paths),
            "planner_blocked_task_paths": list(self.planner_blocked_task_paths),
            "planner_deferred_task_paths": list(self.planner_deferred_task_paths),
            "planner_skipped_task_paths": list(self.planner_skipped_task_paths),
            "planner_rerun_required_task_paths": list(self.planner_rerun_required_task_paths),
            "planner_blocking_reasons": {task_path: reason for task_path, reason in self.planner_blocking_reasons},
        }


@dataclass(frozen=True)
class BatchTaskState:
    task_path: str
    ordinal: int
    status: QueueStatus
    status_note: str
    attempts: int
    updated_seq: int
    depends_on: tuple[str, ...] = ()
    blocks: tuple[str, ...] = ()
    deferrable: bool = False
    skipped_by_policy: bool = False
    rerun_required: bool = False


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
    verification_authority_profile: str = "local_only"
    required_checks_configured: bool = False
    required_checks_discovered: bool = False
    required_checks_missing: bool = False
    required_checks_pending: bool = False
    required_checks_timed_out: bool = False
    required_checks_failed: bool = False
    missing_required_checks_blocks_merge: bool = False
    verification_authority_satisfied: bool = True
    hosted_checks_source: str = "not_required"
    hosted_checks_reported: bool = False
    hosted_authority_available: bool = True
    hosted_authority_satisfied: bool = True
    active_role: str = "controller"
    prior_role: str = ""
    role_attempt_count: int = 0
    handoff_reason: str = ""
    handoff_summary: str = ""
    handoff_instructions: str = ""
    role_output_summary: str = ""
    verifier_verdict: str = "not_run"
    controller_next_role_decision: str = "builder"
    role_outcome: str = "not_run"
    planner_selected_task_path: str = ""
    planner_reordered: bool = False
    planner_ready_task_paths: tuple[str, ...] = ()
    planner_blocked_task_paths: tuple[str, ...] = ()
    planner_deferred_task_paths: tuple[str, ...] = ()
    planner_skipped_task_paths: tuple[str, ...] = ()
    planner_rerun_required_task_paths: tuple[str, ...] = ()
    planner_blocking_reasons: tuple[tuple[str, str], ...] = ()

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
                    "depends_on": list(item.depends_on),
                    "blocks": list(item.blocks),
                    "deferrable": item.deferrable,
                    "skipped_by_policy": item.skipped_by_policy,
                    "rerun_required": item.rerun_required,
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
            "verification_authority_profile": self.verification_authority_profile,
            "required_checks_configured": self.required_checks_configured,
            "required_checks_discovered": self.required_checks_discovered,
            "required_checks_missing": self.required_checks_missing,
            "required_checks_pending": self.required_checks_pending,
            "required_checks_timed_out": self.required_checks_timed_out,
            "required_checks_failed": self.required_checks_failed,
            "missing_required_checks_blocks_merge": self.missing_required_checks_blocks_merge,
            "verification_authority_satisfied": self.verification_authority_satisfied,
            "active_role": self.active_role,
            "prior_role": self.prior_role,
            "role_attempt_count": self.role_attempt_count,
            "handoff_reason": self.handoff_reason,
            "handoff_summary": self.handoff_summary,
            "handoff_instructions": self.handoff_instructions,
            "role_output_summary": self.role_output_summary,
            "verifier_verdict": self.verifier_verdict,
            "controller_next_role_decision": self.controller_next_role_decision,
            "role_outcome": self.role_outcome,
            "planner_selected_task_path": self.planner_selected_task_path,
            "planner_reordered": self.planner_reordered,
            "planner_ready_task_paths": list(self.planner_ready_task_paths),
            "planner_blocked_task_paths": list(self.planner_blocked_task_paths),
            "planner_deferred_task_paths": list(self.planner_deferred_task_paths),
            "planner_skipped_task_paths": list(self.planner_skipped_task_paths),
            "planner_rerun_required_task_paths": list(self.planner_rerun_required_task_paths),
            "planner_blocking_reasons": {task_path: reason for task_path, reason in self.planner_blocking_reasons},
        }



def manifest_fingerprint(manifest: dict[str, Any]) -> str:
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()



def last_checkpoint_for_task(state: BatchState, task_path: str) -> BatchTaskCheckpoint | None:
    for checkpoint in reversed(state.checkpoints):
        if checkpoint.task_path == task_path:
            return checkpoint
    return None



def _queue_items_for_planner(queue_state: tuple[BatchTaskState, ...]) -> list[TaskQueueItem]:
    return [
        TaskQueueItem(
            task_path=item.task_path,
            ordinal=item.ordinal,
            status=item.status,
            status_note=item.status_note,
            depends_on=item.depends_on,
            blocks=item.blocks,
            deferrable=item.deferrable,
            skipped_by_policy=item.skipped_by_policy,
            rerun_required=item.rerun_required,
        )
        for item in queue_state
    ]


def _planner_truth_from_queue(queue_state: tuple[BatchTaskState, ...]) -> dict[str, object]:
    return dict(plan_manifest_progress(_queue_items_for_planner(queue_state)))


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
            depends_on=item.depends_on,
            blocks=item.blocks,
            deferrable=item.deferrable,
            skipped_by_policy=item.skipped_by_policy,
            rerun_required=item.rerun_required,
        )
        for item in queue
    )
    handoff = canonical_role_handoff_state(
        active_role="controller",
        handoff_reason="initial_controller_entry",
        handoff_summary="Controller owns the next-role decision until a specialized role is chosen.",
        controller_next_role_decision="builder",
        role_outcome="controller_routed",
    )
    planner = _planner_truth_from_queue(queue_state)
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
        verification_authority_profile="local_only",
        required_checks_configured=False,
        required_checks_discovered=False,
        required_checks_missing=False,
        required_checks_pending=False,
        required_checks_timed_out=False,
        required_checks_failed=False,
        missing_required_checks_blocks_merge=False,
        verification_authority_satisfied=True,
        hosted_checks_source="not_required",
        hosted_checks_reported=False,
        hosted_authority_available=True,
        hosted_authority_satisfied=True,
        active_role=str(handoff["active_role"]),
        prior_role=str(handoff["prior_role"]),
        role_attempt_count=int(handoff["role_attempt_count"]),
        handoff_reason=str(handoff["handoff_reason"]),
        handoff_summary=str(handoff["handoff_summary"]),
        handoff_instructions=str(handoff["handoff_instructions"]),
        role_output_summary=str(handoff["role_output_summary"]),
        verifier_verdict=str(handoff["verifier_verdict"]),
        controller_next_role_decision=str(handoff["controller_next_role_decision"]),
        role_outcome=str(handoff["role_outcome"]),
        planner_selected_task_path=str(planner["selected_task_path"]),
        planner_reordered=bool(planner["reordered"]),
        planner_ready_task_paths=tuple(str(p) for p in planner["ready_task_paths"]),
        planner_blocked_task_paths=tuple(str(p) for p in planner["blocked_task_paths"]),
        planner_deferred_task_paths=tuple(str(p) for p in planner["deferred_task_paths"]),
        planner_skipped_task_paths=tuple(str(p) for p in planner["skipped_task_paths"]),
        planner_rerun_required_task_paths=tuple(str(p) for p in planner["rerun_required_task_paths"]),
        planner_blocking_reasons=tuple(sorted((str(k), str(v)) for k, v in dict(planner["blocking_reasons"]).items())),
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

    planner = _planner_truth_from_queue(queue_state)
    return replace(
        state,
        queue=queue_state,
        current_index=next_index,
        event_seq=new_seq,
        updated_ts=event_ts or state.updated_ts,
        batch_status=_derive_batch_status(queue_state),
        planner_selected_task_path=str(planner["selected_task_path"]),
        planner_reordered=bool(planner["reordered"]),
        planner_ready_task_paths=tuple(str(p) for p in planner["ready_task_paths"]),
        planner_blocked_task_paths=tuple(str(p) for p in planner["blocked_task_paths"]),
        planner_deferred_task_paths=tuple(str(p) for p in planner["deferred_task_paths"]),
        planner_skipped_task_paths=tuple(str(p) for p in planner["skipped_task_paths"]),
        planner_rerun_required_task_paths=tuple(str(p) for p in planner["rerun_required_task_paths"]),
        planner_blocking_reasons=tuple(sorted((str(k), str(v)) for k, v in dict(planner["blocking_reasons"]).items())),
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
    retry_count: int = 0,
    next_task_may_proceed: bool | None = None,
    accepted_task_pr_flow_completed: bool | None = None,
    required_checks_passed: bool | None = None,
    merged_to_main: bool | None = None,
    clean_main_reset_completed: bool | None = None,
    verification_authority_profile: str | None = None,
    required_checks_discovered: bool | None = None,
    required_checks_missing: bool | None = None,
    required_checks_pending: bool | None = None,
    required_checks_timed_out: bool | None = None,
    required_checks_failed: bool | None = None,
    missing_required_checks_blocks_merge: bool | None = None,
    active_role: str | None = None,
    prior_role: str | None = None,
    role_attempt_count: int | None = None,
    handoff_reason: str | None = None,
    handoff_summary: str | None = None,
    handoff_instructions: str | None = None,
    role_output_summary: str | None = None,
    verifier_verdict: str | None = None,
    controller_next_role_decision: str | None = None,
    role_outcome: str | None = None,
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

    merge_truth = canonical_merge_posture_truth(
        accepted_task_pr_flow_completed=accepted_task_pr_flow_completed,
        required_checks_passed=required_checks_passed,
        merged_to_main=merged_to_main,
        clean_main_reset_completed=clean_main_reset_completed,
    )
    authority_truth = canonical_required_check_truth(
        verification_authority_profile=(verification_authority_profile if verification_authority_profile is not None else state.verification_authority_profile),
        required_checks_discovered=required_checks_discovered if required_checks_discovered is not None else state.required_checks_discovered,
        required_checks_missing=required_checks_missing if required_checks_missing is not None else state.required_checks_missing,
        required_checks_pending=required_checks_pending if required_checks_pending is not None else state.required_checks_pending,
        required_checks_timed_out=required_checks_timed_out if required_checks_timed_out is not None else state.required_checks_timed_out,
        required_checks_failed=required_checks_failed if required_checks_failed is not None else state.required_checks_failed,
        required_checks_passed=merge_truth["required_checks_passed"],
        missing_required_checks_blocks_merge=(missing_required_checks_blocks_merge if missing_required_checks_blocks_merge is not None else state.missing_required_checks_blocks_merge),
    )

    role_state = canonical_role_handoff_state(
        active_role=active_role if active_role is not None else state.active_role,
        prior_role=prior_role if prior_role is not None else state.prior_role,
        role_attempt_count=role_attempt_count if role_attempt_count is not None else state.role_attempt_count,
        handoff_reason=handoff_reason if handoff_reason is not None else state.handoff_reason,
        handoff_summary=handoff_summary if handoff_summary is not None else state.handoff_summary,
        handoff_instructions=handoff_instructions if handoff_instructions is not None else state.handoff_instructions,
        role_output_summary=role_output_summary if role_output_summary is not None else state.role_output_summary,
        verifier_verdict=verifier_verdict if verifier_verdict is not None else state.verifier_verdict,
        controller_next_role_decision=(
            controller_next_role_decision if controller_next_role_decision is not None else state.controller_next_role_decision
        ),
        role_outcome=role_outcome if role_outcome is not None else state.role_outcome,
    )

    planner = _planner_truth_from_queue(state.queue)

    checkpoint = BatchTaskCheckpoint(
        task_path=current.task_path,
        ordinal=current.ordinal,
        context_kind=context_kind,
        context_ref=context_ref,
        terminal_status=terminal_status,
        completed_cleanly=terminal_status == "completed",
        cleanup_required_before_next_task=terminal_status != "completed" or not bool(next_task_may_proceed),
        next_task_may_proceed=bool(next_task_may_proceed),
        transition=transition,
        note=note,
        event_seq=state.event_seq,
        post_task_decision=post_task_decision,
        acceptance_decision=acceptance_decision,
        retry_count=int(retry_count),
        accepted_task_pr_flow_completed=merge_truth["accepted_task_pr_flow_completed"],
        required_checks_passed=merge_truth["required_checks_passed"],
        merged_to_main=merge_truth["merged_to_main"],
        clean_main_reset_completed=merge_truth["clean_main_reset_completed"],
        verification_authority_profile=str(authority_truth["verification_authority_profile"]),
        required_checks_configured=bool(authority_truth["required_checks_configured"]),
        required_checks_discovered=bool(authority_truth["required_checks_discovered"]),
        required_checks_missing=bool(authority_truth["required_checks_missing"]),
        required_checks_pending=bool(authority_truth["required_checks_pending"]),
        required_checks_timed_out=bool(authority_truth["required_checks_timed_out"]),
        required_checks_failed=bool(authority_truth["required_checks_failed"]),
        missing_required_checks_blocks_merge=bool(authority_truth["missing_required_checks_blocks_merge"]),
        verification_authority_satisfied=bool(authority_truth["verification_authority_satisfied"]),
        hosted_checks_source=str(authority_truth["hosted_checks_source"]),
        hosted_checks_reported=bool(authority_truth["hosted_checks_reported"]),
        hosted_authority_available=bool(authority_truth["hosted_authority_available"]),
        hosted_authority_satisfied=bool(authority_truth["hosted_authority_satisfied"]),
        active_role=str(role_state["active_role"]),
        prior_role=str(role_state["prior_role"]),
        role_attempt_count=int(role_state["role_attempt_count"]),
        handoff_reason=str(role_state["handoff_reason"]),
        handoff_summary=str(role_state["handoff_summary"]),
        handoff_instructions=str(role_state["handoff_instructions"]),
        role_output_summary=str(role_state["role_output_summary"]),
        verifier_verdict=str(role_state["verifier_verdict"]),
        controller_next_role_decision=str(role_state["controller_next_role_decision"]),
        role_outcome=str(role_state["role_outcome"]),
        planner_selected_task_path=str(planner["selected_task_path"]),
        planner_reordered=bool(planner["reordered"]),
        planner_ready_task_paths=tuple(str(p) for p in planner["ready_task_paths"]),
        planner_blocked_task_paths=tuple(str(p) for p in planner["blocked_task_paths"]),
        planner_deferred_task_paths=tuple(str(p) for p in planner["deferred_task_paths"]),
        planner_skipped_task_paths=tuple(str(p) for p in planner["skipped_task_paths"]),
        planner_rerun_required_task_paths=tuple(str(p) for p in planner["rerun_required_task_paths"]),
        planner_blocking_reasons=tuple(sorted((str(k), str(v)) for k, v in dict(planner["blocking_reasons"]).items())),
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
        verification_authority_profile=str(authority_truth["verification_authority_profile"]),
        required_checks_configured=bool(authority_truth["required_checks_configured"]),
        required_checks_discovered=bool(authority_truth["required_checks_discovered"]),
        required_checks_missing=bool(authority_truth["required_checks_missing"]),
        required_checks_pending=bool(authority_truth["required_checks_pending"]),
        required_checks_timed_out=bool(authority_truth["required_checks_timed_out"]),
        required_checks_failed=bool(authority_truth["required_checks_failed"]),
        missing_required_checks_blocks_merge=bool(authority_truth["missing_required_checks_blocks_merge"]),
        verification_authority_satisfied=bool(authority_truth["verification_authority_satisfied"]),
        active_role=str(role_state["active_role"]),
        prior_role=str(role_state["prior_role"]),
        role_attempt_count=int(role_state["role_attempt_count"]),
        handoff_reason=str(role_state["handoff_reason"]),
        handoff_summary=str(role_state["handoff_summary"]),
        handoff_instructions=str(role_state["handoff_instructions"]),
        role_output_summary=str(role_state["role_output_summary"]),
        verifier_verdict=str(role_state["verifier_verdict"]),
        controller_next_role_decision=str(role_state["controller_next_role_decision"]),
        role_outcome=str(role_state["role_outcome"]),
        planner_selected_task_path=str(planner["selected_task_path"]),
        planner_reordered=bool(planner["reordered"]),
        planner_ready_task_paths=tuple(str(p) for p in planner["ready_task_paths"]),
        planner_blocked_task_paths=tuple(str(p) for p in planner["blocked_task_paths"]),
        planner_deferred_task_paths=tuple(str(p) for p in planner["deferred_task_paths"]),
        planner_skipped_task_paths=tuple(str(p) for p in planner["skipped_task_paths"]),
        planner_rerun_required_task_paths=tuple(str(p) for p in planner["rerun_required_task_paths"]),
        planner_blocking_reasons=tuple(sorted((str(k), str(v)) for k, v in dict(planner["blocking_reasons"]).items())),
    )



def _resume_index_for_task(queue: list[TaskQueueItem], task_path: str) -> int | None:
    for idx, item in enumerate(queue):
        if item.task_path == task_path:
            return idx
    return None



def _reset_queue_for_resume(
    queue_state: tuple[BatchTaskState, ...],
    *,
    from_index: int,
    status_note: str,
) -> tuple[BatchTaskState, ...]:
    items = list(queue_state)
    for idx in range(from_index, len(items)):
        items[idx] = replace(items[idx], status="queued", status_note=status_note)
    return tuple(items)



def unresolved_manual_resolution_task_path(state: BatchState) -> str:
    for checkpoint in reversed(state.checkpoints):
        if checkpoint_requires_manual_resolution(checkpoint.to_dict()):
            return checkpoint.task_path
    return ""



def _resume_after_merge_rewind_index(state: BatchState) -> int | None:
    for idx, item in enumerate(state.queue[: state.current_index]):
        if item.status != "completed":
            continue
        checkpoint = last_checkpoint_for_task(state, item.task_path)
        if not checkpoint_allows_resume_after_merge(checkpoint.to_dict() if checkpoint is not None else None):
            return idx
    return None



def current_role_handoff_state(state: BatchState) -> dict[str, object]:
    return canonical_role_handoff_state(
        active_role=state.active_role,
        prior_role=state.prior_role,
        role_attempt_count=state.role_attempt_count,
        handoff_reason=state.handoff_reason,
        handoff_summary=state.handoff_summary,
        handoff_instructions=state.handoff_instructions,
        role_output_summary=state.role_output_summary,
        verifier_verdict=state.verifier_verdict,
        controller_next_role_decision=state.controller_next_role_decision,
        role_outcome=state.role_outcome,
    )


def resume_role_handoff_state_for_batch(state: BatchState, *, task_path: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = current_role_handoff_state(state)
    target = str(task_path or state.resume_target_task_path or "")
    if target:
        checkpoint = last_checkpoint_for_task(state, target)
        if checkpoint is not None:
            payload = checkpoint.to_dict()
    return resume_role_handoff_state(payload)


def mark_resume_plan(
    state: BatchState,
    *,
    queue: list[TaskQueueItem],
    resume_mode: ResumeMode,
    resume_target_task_path: str | None,
    explicit_resume: bool,
    updated_ts: int,
) -> BatchState:
    inferred_target = str(resume_target_task_path or "")
    if resume_mode == "resume_after_manual_resolution" and not inferred_target:
        inferred_target = unresolved_manual_resolution_task_path(state)
    metadata = canonical_resume_metadata(
        resume_mode=resume_mode,
        resume_target_task_path=inferred_target,
        explicit_resume=explicit_resume,
    )
    next_index = state.current_index
    queue_state = state.queue
    if resume_mode == "resume_after_merge":
        rewind_index = _resume_after_merge_rewind_index(state)
        if rewind_index is not None:
            next_index = rewind_index
            queue_state = _reset_queue_for_resume(queue_state, from_index=rewind_index, status_note="resume_after_merge")
    if resume_mode == "resume_after_manual_resolution" and explicit_resume and metadata["resume_target_task_path"]:
        resolved_index = _resume_index_for_task(queue, metadata["resume_target_task_path"])
        if resolved_index is not None:
            next_index = resolved_index
            queue_state = _reset_queue_for_resume(queue_state, from_index=resolved_index, status_note="resume_after_manual_resolution")
    resumed_role = resume_role_handoff_state_for_batch(state, task_path=metadata["resume_target_task_path"] or None)
    return replace(
        state,
        queue=queue_state,
        current_index=next_index,
        resume_reason=metadata["resume_reason"],
        resume_target_task_path=metadata["resume_target_task_path"],
        resume_gate=metadata["resume_gate"],
        updated_ts=updated_ts,
        verification_authority_profile=state.verification_authority_profile,
        required_checks_configured=state.required_checks_configured,
        required_checks_discovered=state.required_checks_discovered,
        required_checks_missing=state.required_checks_missing,
        required_checks_pending=state.required_checks_pending,
        required_checks_timed_out=state.required_checks_timed_out,
        required_checks_failed=state.required_checks_failed,
        missing_required_checks_blocks_merge=state.missing_required_checks_blocks_merge,
        verification_authority_satisfied=state.verification_authority_satisfied,
        hosted_checks_source=state.hosted_checks_source,
        hosted_checks_reported=state.hosted_checks_reported,
        hosted_authority_available=state.hosted_authority_available,
        hosted_authority_satisfied=state.hosted_authority_satisfied,
        planner_selected_task_path=state.planner_selected_task_path,
        planner_reordered=state.planner_reordered,
        planner_ready_task_paths=state.planner_ready_task_paths,
        planner_blocked_task_paths=state.planner_blocked_task_paths,
        planner_deferred_task_paths=state.planner_deferred_task_paths,
        planner_skipped_task_paths=state.planner_skipped_task_paths,
        planner_rerun_required_task_paths=state.planner_rerun_required_task_paths,
        planner_blocking_reasons=state.planner_blocking_reasons,
        active_role=str(resumed_role["active_role"]),
        prior_role=str(resumed_role["prior_role"]),
        role_attempt_count=int(resumed_role["role_attempt_count"]),
        handoff_reason=str(resumed_role["handoff_reason"]),
        handoff_summary=str(resumed_role["handoff_summary"]),
        handoff_instructions=str(resumed_role["handoff_instructions"]),
        role_output_summary=str(resumed_role["role_output_summary"]),
        verifier_verdict=str(resumed_role["verifier_verdict"]),
        controller_next_role_decision=str(resumed_role["controller_next_role_decision"]),
        role_outcome=str(resumed_role["role_outcome"]),
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
