from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from agents.lib import batch_state as bs
from agents.lib.final_acceptance import AcceptanceDecision
from agents.lib.task_queue import BatchPostTaskDecision, QueueStatus, TaskQueueItem


@dataclass(frozen=True)
class BatchTaskOutcome:
    task_path: str
    terminal_status: QueueStatus
    acceptance_decision: AcceptanceDecision
    retry_count: int
    next_task_may_proceed: bool
    post_task_decision: BatchPostTaskDecision
    note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "task_path": self.task_path,
            "terminal_status": self.terminal_status,
            "acceptance_decision": self.acceptance_decision,
            "retry_count": self.retry_count,
            "next_task_may_proceed": self.next_task_may_proceed,
            "post_task_decision": self.post_task_decision,
            "note": self.note,
        }


def _coerce_acceptance(payload: dict[str, Any]) -> tuple[AcceptanceDecision, str]:
    decision = str(payload.get("acceptance_decision", "retryable_failure")).strip() or "retryable_failure"
    if decision not in {"accepted", "retryable_failure", "manual_patch", "blocked"}:
        decision = "retryable_failure"
    note = str(payload.get("note", "")).strip()
    return decision, note


def _map_acceptance_to_terminal(decision: AcceptanceDecision) -> QueueStatus:
    if decision == "accepted":
        return "completed"
    if decision == "manual_patch":
        return "manual_patch"
    if decision == "blocked":
        return "blocked"
    return "failed"


def _map_terminal_to_post_task_decision(status: QueueStatus) -> BatchPostTaskDecision:
    if status == "completed":
        return "continue"
    if status == "manual_patch":
        return "manual_patch"
    if status == "blocked":
        return "blocked"
    return "stop"


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
) -> tuple[bs.BatchState, list[dict[str, object]], BatchPostTaskDecision]:
    state = initial_state
    outcomes: list[dict[str, object]] = []
    final_decision: BatchPostTaskDecision = "stop"

    for item in queue:
        if item.ordinal - 1 < state.current_index:
            continue

        retry_count = 0
        accepted = False
        acceptance_decision: AcceptanceDecision = "retryable_failure"
        acceptance_note = ""
        result: dict[str, Any] = {}

        state = bs.advance_task_status(
            state,
            task_index=item.ordinal - 1,
            to_status="running",
            status_note="running",
            event_ts=state.updated_ts + 1,
        )
        persist_state(state)

        while True:
            result = execute_task(item)
            validator_ok, validator_note = run_authoritative_validation(item, result)
            acceptance_payload = run_final_acceptance_review(item, result, validator_ok, validator_note)
            acceptance_decision, acceptance_note = _coerce_acceptance(acceptance_payload)

            if acceptance_decision == "accepted":
                accepted = True
                break

            if acceptance_decision == "retryable_failure" and retry_count < max(0, int(retry_budget)):
                retry_count += 1
                result = self_heal_and_retry(item, result, retry_count)
                continue

            break

        terminal_status = _map_acceptance_to_terminal(acceptance_decision)
        post_task_decision = _map_terminal_to_post_task_decision(terminal_status)
        may_proceed = terminal_status == "completed"

        state = bs.apply_task_result(
            state,
            task_path=item.task_path,
            terminal_status=terminal_status,
            post_task_decision=post_task_decision,
            note=acceptance_note or ("accepted" if accepted else "not accepted"),
            updated_ts=state.updated_ts + 1,
            context_kind="branch",
            context_ref="batch-executor",
            acceptance_decision=acceptance_decision,
            retry_count=retry_count,
            next_task_may_proceed=may_proceed,
        )
        persist_state(state)

        outcome = BatchTaskOutcome(
            task_path=item.task_path,
            terminal_status=terminal_status,
            acceptance_decision=acceptance_decision,
            retry_count=retry_count,
            next_task_may_proceed=may_proceed,
            post_task_decision=post_task_decision,
            note=acceptance_note or "",
        )
        outcomes.append(outcome.to_dict())

        final_decision = post_task_decision
        if final_decision in {"manual_patch", "blocked", "stop"}:
            break

    if final_decision == "stop" and state.batch_status == "completed":
        final_decision = "continue"

    return state, outcomes, final_decision
