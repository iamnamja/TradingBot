from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable

from agents.lib import batch_state as bs
from agents.lib.controller_contract import (
    AcceptanceDecision,
    BatchPostTaskDecision,
    ResumeMode,
    acceptance_decision_to_terminal_status,
    canonical_merge_posture_truth,
    checkpoint_allows_resume_after_merge,
    checkpoint_requires_manual_resolution,
    coerce_acceptance_decision,
    coerce_post_task_decision,
    resume_mode_allows_execution,
    should_next_task_proceed,
    terminal_status_to_post_task_decision,
    coerce_batch_status,
)
from agents.lib.task_queue import QueueStatus, TaskQueueItem


@dataclass(frozen=True)
class BatchTaskOutcome:
    task_path: str
    terminal_status: QueueStatus
    acceptance_decision: AcceptanceDecision
    retry_count: int
    next_task_may_proceed: bool
    post_task_decision: BatchPostTaskDecision
    note: str
    accepted_task_pr_flow_completed: bool = False
    required_checks_passed: bool = False
    merged_to_main: bool = False
    clean_main_reset_completed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "task_path": self.task_path,
            "terminal_status": self.terminal_status,
            "acceptance_decision": self.acceptance_decision,
            "retry_count": self.retry_count,
            "next_task_may_proceed": self.next_task_may_proceed,
            "post_task_decision": self.post_task_decision,
            "note": self.note,
            "accepted_task_pr_flow_completed": self.accepted_task_pr_flow_completed,
            "required_checks_passed": self.required_checks_passed,
            "merged_to_main": self.merged_to_main,
            "clean_main_reset_completed": self.clean_main_reset_completed,
        }



def _coerce_acceptance(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["acceptance_decision"] = coerce_acceptance_decision(payload.get("acceptance_decision"))
    out["note"] = str(payload.get("note", "")).strip()
    if "post_task_decision" in payload:
        out["post_task_decision"] = coerce_post_task_decision(payload.get("post_task_decision"))
    out.update(canonical_merge_posture_truth(payload))
    return out



def _skip_eligible_for_resume_after_merge(item: TaskQueueItem, state: bs.BatchState) -> bool:
    idx = item.ordinal - 1
    if idx < 0 or idx >= len(state.queue):
        return False
    if state.queue[idx].status != "completed":
        return False
    checkpoint = bs.last_checkpoint_for_task(state, item.task_path)
    return checkpoint_allows_resume_after_merge(checkpoint.to_dict() if checkpoint is not None else None)



def _resume_ready_state(
    *,
    state: bs.BatchState,
    queue: list[TaskQueueItem],
    resume_mode: ResumeMode,
    resume_target_task_path: str | None,
    explicit_resume: bool,
) -> bs.BatchState:
    if resume_mode == "default":
        return state
    return bs.mark_resume_plan(
        state,
        queue=queue,
        resume_mode=resume_mode,
        resume_target_task_path=resume_target_task_path,
        explicit_resume=explicit_resume or resume_mode == "resume_after_merge",
        updated_ts=state.updated_ts + 1,
    )



def prepare_resumed_batch_state(
    *,
    state: bs.BatchState,
    queue: list[TaskQueueItem],
    resume_mode: ResumeMode = "default",
    resume_target_task_path: str | None = None,
    explicit_resume: bool = False,
) -> bs.BatchState:
    return _resume_ready_state(
        state=state,
        queue=queue,
        resume_mode=resume_mode,
        resume_target_task_path=resume_target_task_path,
        explicit_resume=explicit_resume,
    )



def should_skip_completed_accepted_task(item: TaskQueueItem, state: bs.BatchState) -> bool:
    return _skip_eligible_for_resume_after_merge(item, state)



def _blocking_resume_decision(state: bs.BatchState) -> BatchPostTaskDecision:
    for checkpoint in reversed(state.checkpoints):
        if checkpoint_requires_manual_resolution(checkpoint.to_dict()):
            return coerce_post_task_decision(checkpoint.post_task_decision, default="manual_patch")
    return "manual_patch"


def execute_batch_loop(
    *,
    initial_state: bs.BatchState,
    queue: list[TaskQueueItem],
    execute_task: Callable[[TaskQueueItem], dict[str, Any]],
    run_authoritative_validation: Callable[[TaskQueueItem, dict[str, Any]], tuple[bool, str]],
    run_final_acceptance_review: Callable[[TaskQueueItem, dict[str, Any], bool, str], dict[str, Any]],
    self_heal_and_retry: Callable[[TaskQueueItem, dict[str, Any], int], dict[str, Any]],
    retry_budget: int,
    persist_state: Callable[[bs.BatchState], None],
    resume_mode: ResumeMode = "default",
    resume_target_task_path: str | None = None,
    explicit_resume: bool = False,
) -> tuple[bs.BatchState, list[dict[str, object]], BatchPostTaskDecision]:
    state = _resume_ready_state(
        state=initial_state,
        queue=queue,
        resume_mode=resume_mode,
        resume_target_task_path=resume_target_task_path,
        explicit_resume=explicit_resume,
    )
    if state is not initial_state:
        persist_state(state)

    if not resume_mode_allows_execution(resume_mode=resume_mode, explicit_resume=explicit_resume):
        return state, [], _blocking_resume_decision(state)

    outcomes: list[dict[str, object]] = []
    final_decision: BatchPostTaskDecision = "stop"

    for item in queue:
        if item.ordinal - 1 < state.current_index:
            continue

        if resume_mode == "resume_after_merge" and _skip_eligible_for_resume_after_merge(item, state):
            state = bs.record_resume_skip(
                state,
                task_path=item.task_path,
                reason="skip_accepted_merged",
                updated_ts=state.updated_ts + 1,
            )
            persist_state(state)
            continue

        retry_count = 0
        accepted = False
        acceptance_payload: dict[str, Any] = {
            "acceptance_decision": "retryable_failure",
            "note": "",
        }

        result = execute_task(item)
        state = bs.advance_task_status(
            state,
            task_index=item.ordinal - 1,
            to_status="running",
            status_note="running",
            event_ts=state.updated_ts + 1,
        )
        persist_state(state)

        while True:
            validator_ok, validator_note = run_authoritative_validation(item, result)
            acceptance_payload = _coerce_acceptance(
                run_final_acceptance_review(item, result, validator_ok, validator_note)
            )
            decision = acceptance_payload["acceptance_decision"]

            if decision == "accepted":
                accepted = True
                break

            if decision == "retryable_failure" and retry_count < max(0, int(retry_budget)):
                retry_count += 1
                result = self_heal_and_retry(item, result, retry_count)
                continue

            break

        terminal_status = acceptance_decision_to_terminal_status(acceptance_payload["acceptance_decision"])
        post_task_decision = coerce_post_task_decision(
            acceptance_payload.get("post_task_decision"),
            default=terminal_status_to_post_task_decision(terminal_status),
        )
        may_proceed = bool(
            acceptance_payload.get(
                "next_task_may_proceed",
                should_next_task_proceed(terminal_status=terminal_status, post_task_decision=post_task_decision),
            )
        )
        pr_flow_kwargs = canonical_merge_posture_truth(acceptance_payload)

        state = bs.apply_task_result(
            state,
            task_path=item.task_path,
            terminal_status=terminal_status,
            post_task_decision=post_task_decision,
            note=acceptance_payload.get("note") or ("accepted" if accepted else "not accepted"),
            updated_ts=state.updated_ts + 1,
            context_kind="branch",
            context_ref="batch-executor",
            acceptance_decision=acceptance_payload["acceptance_decision"],
            retry_count=retry_count,
            next_task_may_proceed=may_proceed,
            **pr_flow_kwargs,
        )
        persist_state(state)

        outcome = BatchTaskOutcome(
            task_path=item.task_path,
            terminal_status=terminal_status,
            acceptance_decision=acceptance_payload["acceptance_decision"],
            retry_count=retry_count,
            next_task_may_proceed=may_proceed,
            post_task_decision=post_task_decision,
            note=acceptance_payload.get("note", ""),
            accepted_task_pr_flow_completed=pr_flow_kwargs["accepted_task_pr_flow_completed"],
            required_checks_passed=pr_flow_kwargs["required_checks_passed"],
            merged_to_main=pr_flow_kwargs["merged_to_main"],
            clean_main_reset_completed=pr_flow_kwargs["clean_main_reset_completed"],
        )
        outcomes.append(outcome.to_dict())

        final_decision = post_task_decision
        if final_decision != "continue":
            break

    if final_decision == "stop" and state.batch_status == "completed":
        final_decision = "continue"
    normalized_status = coerce_batch_status(state.batch_status, default="failed")
    if normalized_status != state.batch_status:
        state = replace(state, batch_status=normalized_status)
    return state, outcomes, final_decision
