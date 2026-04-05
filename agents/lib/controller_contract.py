from __future__ import annotations

from typing import Any, Literal, Mapping, cast

AcceptanceDecision = Literal["accepted", "retryable_failure", "manual_patch", "blocked"]
BatchPostTaskDecision = Literal[
    "continue",
    "stop",
    "manual_patch",
    "blocked",
    "failed_merge",
    "failed_checks",
    "failed_reset",
]
BatchStatus = Literal[
    "active",
    "completed",
    "blocked",
    "failed",
    "manual_patch",
    "failed_merge",
    "failed_checks",
    "failed_reset",
]
ResumeMode = Literal[
    "default",
    "resume_same_task",
    "resume_next",
    "resume_after_merge",
    "resume_after_manual_resolution",
]
QueueTerminalStatus = Literal["completed", "failed", "manual_patch", "blocked"]

ACCEPTANCE_DECISIONS: tuple[AcceptanceDecision, ...] = (
    "accepted",
    "retryable_failure",
    "manual_patch",
    "blocked",
)
POST_TASK_DECISIONS: tuple[BatchPostTaskDecision, ...] = (
    "continue",
    "stop",
    "manual_patch",
    "blocked",
    "failed_merge",
    "failed_checks",
    "failed_reset",
)
RESUME_MODES: tuple[ResumeMode, ...] = (
    "default",
    "resume_same_task",
    "resume_next",
    "resume_after_merge",
    "resume_after_manual_resolution",
)
QUEUE_TERMINAL_STATUSES: tuple[QueueTerminalStatus, ...] = (
    "completed",
    "failed",
    "manual_patch",
    "blocked",
)
MERGE_POSTURE_POST_TASK_DECISIONS: tuple[BatchPostTaskDecision, ...] = (
    "failed_merge",
    "failed_checks",
    "failed_reset",
)
MERGE_POSTURE_BATCH_STATUSES: tuple[BatchStatus, ...] = cast(
    tuple[BatchStatus, ...], MERGE_POSTURE_POST_TASK_DECISIONS
)

EXECUTION_AUDIT_FIELDS: tuple[str, ...] = (
    "execution_attempt_count",
    "repair_count",
    "accepted_after_repair",
)
CHECKPOINT_TRUTH_FIELDS: tuple[str, ...] = (
    "task_path",
    "ordinal",
    "context_kind",
    "context_ref",
    "completed_cleanly",
    "cleanup_required_before_next_task",
    "next_task_may_proceed",
    "transition",
    "note",
    "event_seq",
    "post_task_decision",
    "acceptance_decision",
    "execution_attempt_count",
    "repair_count",
    "accepted_after_repair",
    "retry_count",
    "accepted_task_pr_flow_completed",
    "required_checks_passed",
    "merged_to_main",
    "clean_main_reset_completed",
)
RESUME_METADATA_FIELDS: tuple[str, ...] = (
    "resume_reason",
    "resume_target_task_path",
    "resume_gate",
)
PERSISTED_CONTROLLER_FIELD_NAMES: tuple[str, ...] = CHECKPOINT_TRUTH_FIELDS + RESUME_METADATA_FIELDS

POLICY_BLOCKED_FAILURE_CATEGORY = "policy_blocked"
CONTROLLER_FAILURE_CATEGORIES: tuple[str, ...] = (POLICY_BLOCKED_FAILURE_CATEGORY,)

_TERMINAL_FROM_ACCEPTANCE: dict[AcceptanceDecision, QueueTerminalStatus] = {
    "accepted": "completed",
    "retryable_failure": "failed",
    "manual_patch": "manual_patch",
    "blocked": "blocked",
}
_POST_TASK_FROM_TERMINAL: dict[QueueTerminalStatus, BatchPostTaskDecision] = {
    "completed": "continue",
    "failed": "stop",
    "manual_patch": "manual_patch",
    "blocked": "blocked",
}


def coerce_acceptance_decision(value: Any, default: AcceptanceDecision = "retryable_failure") -> AcceptanceDecision:
    text = str(value or "").strip()
    if text in ACCEPTANCE_DECISIONS:
        return cast(AcceptanceDecision, text)
    return default



def coerce_post_task_decision(value: Any, default: BatchPostTaskDecision = "stop") -> BatchPostTaskDecision:
    text = str(value or "").strip()
    if text in POST_TASK_DECISIONS:
        return cast(BatchPostTaskDecision, text)
    return default



def coerce_resume_mode(value: Any, default: ResumeMode = "default") -> ResumeMode:
    text = str(value or "").strip()
    if text in RESUME_MODES:
        return cast(ResumeMode, text)
    return default



def acceptance_decision_to_terminal_status(decision: AcceptanceDecision) -> QueueTerminalStatus:
    return _TERMINAL_FROM_ACCEPTANCE[coerce_acceptance_decision(decision)]



def terminal_status_to_post_task_decision(status: str) -> BatchPostTaskDecision:
    text = str(status or "").strip()
    if text in _POST_TASK_FROM_TERMINAL:
        return _POST_TASK_FROM_TERMINAL[cast(QueueTerminalStatus, text)]
    return "stop"



def should_next_task_proceed(*, terminal_status: str, post_task_decision: str) -> bool:
    return str(terminal_status or "").strip() == "completed" and coerce_post_task_decision(post_task_decision) == "continue"



def is_merge_posture_decision(value: Any) -> bool:
    return coerce_post_task_decision(value, default="stop") in MERGE_POSTURE_POST_TASK_DECISIONS



def batch_status_for_post_task_decision(*, default_status: BatchStatus, post_task_decision: Any) -> BatchStatus:
    decision = coerce_post_task_decision(post_task_decision, default="stop")
    if decision in MERGE_POSTURE_POST_TASK_DECISIONS:
        return cast(BatchStatus, decision)
    return default_status



def merge_posture_decision_for_flow_stage(stage: str) -> BatchPostTaskDecision:
    text = str(stage or "").strip()
    if text == "checks":
        return "failed_checks"
    if text == "reset":
        return "failed_reset"
    return "failed_merge"



def resume_gate_for_mode(*, resume_mode: ResumeMode, explicit_resume: bool) -> str:
    mode = coerce_resume_mode(resume_mode)
    if explicit_resume or mode == "resume_after_merge":
        return mode
    return ""



def canonical_resume_metadata(*, resume_mode: ResumeMode, resume_target_task_path: str | None, explicit_resume: bool) -> dict[str, str]:
    mode = coerce_resume_mode(resume_mode)
    return {
        "resume_reason": mode,
        "resume_target_task_path": str(resume_target_task_path or ""),
        "resume_gate": resume_gate_for_mode(resume_mode=mode, explicit_resume=explicit_resume),
    }



def coerce_non_negative_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return max(0, int(default))
    return max(0, parsed)


def canonical_repair_audit(
    *,
    execution_attempt_count: Any,
    repair_count: Any,
    acceptance_decision: Any,
    accepted_after_repair: Any | None = None,
) -> dict[str, int | bool]:
    execution_count = coerce_non_negative_int(execution_attempt_count)
    repair_total = coerce_non_negative_int(repair_count)
    accepted = coerce_acceptance_decision(acceptance_decision) == "accepted"
    if accepted_after_repair is None:
        repaired_accept = repair_total > 0 and accepted
    else:
        repaired_accept = bool(accepted_after_repair)
    return {
        "execution_attempt_count": execution_count,
        "repair_count": repair_total,
        "accepted_after_repair": repaired_accept,
        "retry_count": repair_total,
    }


def checkpoint_allows_resume_after_merge(checkpoint: Mapping[str, Any] | None) -> bool:
    if not checkpoint:
        return False
    return bool(
        coerce_acceptance_decision(checkpoint.get("acceptance_decision")) == "accepted"
        and checkpoint.get("post_task_decision") == "continue"
        and bool(checkpoint.get("next_task_may_proceed", False))
        and bool(checkpoint.get("merged_to_main", False))
        and bool(checkpoint.get("clean_main_reset_completed", False))
    )



def controller_contract_snapshot() -> dict[str, object]:
    return {
        "acceptance_decisions": list(ACCEPTANCE_DECISIONS),
        "post_task_decisions": list(POST_TASK_DECISIONS),
        "resume_modes": list(RESUME_MODES),
        "execution_audit_fields": list(EXECUTION_AUDIT_FIELDS),
        "checkpoint_truth_fields": list(CHECKPOINT_TRUTH_FIELDS),
        "resume_metadata_fields": list(RESUME_METADATA_FIELDS),
        "controller_failure_categories": list(CONTROLLER_FAILURE_CATEGORIES),
    }
