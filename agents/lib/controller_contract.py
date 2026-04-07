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
MERGE_POSTURE_POST_TASK_DECISIONS: tuple[BatchPostTaskDecision, ...] = (
    "failed_merge",
    "failed_checks",
    "failed_reset",
)
CHECKPOINT_TRUTH_FIELDS: tuple[str, ...] = (
    "task_path",
    "ordinal",
    "context_kind",
    "context_ref",
    "terminal_status",
    "completed_cleanly",
    "cleanup_required_before_next_task",
    "next_task_may_proceed",
    "transition",
    "note",
    "event_seq",
    "post_task_decision",
    "acceptance_decision",
    "retry_count",
    "accepted_task_pr_flow_completed",
    "required_checks_passed",
    "merged_to_main",
    "clean_main_reset_completed",
    "coder_artifact_envelope",
    "tester_artifact_envelope",
    "controller_artifact_envelope",
    "active_role",
    "prior_role",
    "role_attempt_count",
    "handoff_reason",
    "handoff_summary",
    "handoff_instructions",
    "role_output_summary",
    "verifier_verdict",
    "controller_next_role_decision",
    "role_outcome",
)
RESUME_METADATA_FIELDS: tuple[str, ...] = (
    "resume_reason",
    "resume_target_task_path",
    "resume_gate",
)
POLICY_BLOCKED_FAILURE_CATEGORY = "policy_blocked"
CONTROLLER_FAILURE_CATEGORIES: tuple[str, ...] = (POLICY_BLOCKED_FAILURE_CATEGORY,)
CONTROLLER_STRICT_MODE_PATHS: tuple[str, ...] = (
    "agents/run_task.py",
    "agents/lib/controller_contract.py",
    "agents/lib/batch_executor.py",
    "agents/lib/batch_state.py",
    "agents/lib/task_queue.py",
    "agents/lib/final_acceptance.py",
    "agents/lib/failure_journal.py",
    "agents/lib/git_workflow.py",
    "agents/lib/multi_agent_contract.py",
)
CONTROLLER_PROOF_TEST_PATHS: tuple[str, ...] = (
    "tests/test_controller_contract.py",
    "tests/test_run_task_runtime_foundations.py",
    "tests/test_task_queue.py",
)
CONTROLLER_FAMILY_FILES: tuple[str, ...] = (
    "agents/run_task.py",
    "agents/lib/controller_contract.py",
    "agents/lib/controller_repair.py",
    "agents/lib/final_acceptance.py",
    "agents/lib/batch_executor.py",
    "agents/lib/batch_state.py",
    "agents/lib/task_queue.py",
    "agents/lib/git_workflow.py",
    "agents/lib/failure_journal.py",
    "agents/lib/multi_agent_contract.py",
)
CONTROLLER_FAILURE_DIGEST_FIELDS: tuple[str, ...] = (
    "failure_kind",
    "failure_category",
    "is_controller_failure",
    "failing_tests",
    "decision_mismatches",
    "missing_truth_fields",
    "extra_truth_fields",
    "missing_exports",
    "merge_posture_mismatches",
    "taxonomy_mismatches",
    "controller_family_files_touched",
)

CONTROLLER_RUNTIME_DELEGATE_SURFACES: tuple[str, ...] = (
    "build_final_acceptance_report",
    "classify_final_acceptance_failure",
    "build_acceptance_self_heal_context",
    "build_final_acceptance_failure_feedback",
    "build_final_acceptance_retry_feedback",
    "report_final_acceptance_failure",
    "build_controller_failure_digest",
    "build_controller_repair_context",
    "build_controller_test_failure_appendix",
    "build_controller_strict_mode_context",
    "describe_controller_strict_mode",
    "controller_strict_preapply_issues",
    "format_controller_strict_preapply_issues",
    "run_controller_strict_checks",
    "strict_validation_profile",
    "multi_agent_contract_snapshot",
    "canonical_role_handoff_state",
    "canonical_role_artifact_envelope",
    "summarize_role_artifact_envelope",
    "resume_role_handoff_state",
    "controller_decides_next_role",
    "multi_agent_task_context",
)


PROOF_SYNC_RUN_TASK_EXPORTS: tuple[str, ...] = (
    "execute_multi_agent_loop",
    "multi_agent_contract_snapshot",
    "orchestrator_package_boundary_snapshot",
    "proof_sync_contract_snapshot",
    "validate_proof_sync_contract",
)
PROOF_SYNC_MULTI_AGENT_LOOP_EXPORTS: tuple[str, ...] = (
    "execute_multi_agent_loop",
    "run_multi_agent_controller_cycle",
    "run_multi_agent_task_cycle",
)
PROOF_SYNC_COMPAT_RESULT_FIELDS: tuple[str, ...] = (
    "processed_task_ids",
    "verification_authority",
    "controller_final_decision",
    "runtime_portability_scope",
)
PROOF_SYNC_CANONICAL_RESULT_FIELDS: tuple[str, ...] = (
    "builder_artifact",
    "verifier_artifact",
    "controller_decision",
    "role_handoff_state",
)
PROOF_SYNC_ALLOWED_MANIFEST_ENTRY_KEYS: tuple[str, ...] = (
    "path",
    "task_path",
    "task_id",
    "depends_on",
    "blocks",
    "deferrable",
    "skipped_by_policy",
    "rerun_required",
    "label",
    "note",
    "stop_policy",
)
PROOF_SYNC_REQUIRED_BOUNDARY_KEYS: tuple[str, ...] = (
    "product_name",
    "operates_inside_monorepo",
    "full_standalone_extraction_completed",
    "supported_consumers",
)
PROOF_SYNC_REQUIRED_ROLE_SNAPSHOT_KEYS: tuple[str, ...] = (
    "roles",
    "sequential_role_execution_only",
    "controller_authority_over_next_role",
)
PROOF_SYNC_CLAIM_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "arbitrary project creation",
    "broad unattended scheduler autonomy",
    "full standalone extraction completion",
    "broad arbitrary multi-language portability",
    "arbitrary protected/controller task-list autonomy",
)
PROOF_SYNC_CLAIM_GUARD_HINTS: tuple[str, ...] = (
    "bounded",
    "python",
    "does not",
)

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


def coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off", ""}:
        return False
    return bool(value)


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


def canonical_merge_posture_truth(
    payload: Mapping[str, Any] | None = None,
    *,
    accepted_task_pr_flow_completed: Any | None = None,
    required_checks_passed: Any | None = None,
    merged_to_main: Any | None = None,
    clean_main_reset_completed: Any | None = None,
) -> dict[str, bool]:
    data = payload or {}
    checks_passed = coerce_bool(required_checks_passed if required_checks_passed is not None else data.get("required_checks_passed"))
    merged = coerce_bool(merged_to_main if merged_to_main is not None else data.get("merged_to_main", data.get("merged")))
    reset_clean = coerce_bool(
        clean_main_reset_completed if clean_main_reset_completed is not None else data.get("clean_main_reset_completed", data.get("main_reset_clean"))
    )
    raw_completed = accepted_task_pr_flow_completed if accepted_task_pr_flow_completed is not None else data.get("accepted_task_pr_flow_completed")
    completed = coerce_bool(raw_completed) if raw_completed is not None else (checks_passed and merged and reset_clean)
    return {
        "accepted_task_pr_flow_completed": completed,
        "required_checks_passed": checks_passed,
        "merged_to_main": merged,
        "clean_main_reset_completed": reset_clean,
    }


def checkpoint_allows_resume_after_merge(checkpoint: Mapping[str, Any] | None) -> bool:
    if not checkpoint:
        return False
    truth = canonical_merge_posture_truth(checkpoint)
    return bool(
        str(checkpoint.get("terminal_status", "")).strip() == "completed"
        and coerce_acceptance_decision(checkpoint.get("acceptance_decision")) == "accepted"
        and coerce_post_task_decision(checkpoint.get("post_task_decision"), default="stop") == "continue"
        and bool(checkpoint.get("next_task_may_proceed", False))
        and truth["accepted_task_pr_flow_completed"]
        and truth["required_checks_passed"]
        and truth["merged_to_main"]
        and truth["clean_main_reset_completed"]
    )


def checkpoint_requires_manual_resolution(checkpoint: Mapping[str, Any] | None) -> bool:
    if not checkpoint:
        return False
    return coerce_post_task_decision(checkpoint.get("post_task_decision"), default="stop") in {"manual_patch", "blocked"}


def resume_mode_allows_execution(*, resume_mode: ResumeMode, explicit_resume: bool) -> bool:
    mode = coerce_resume_mode(resume_mode)
    if mode == "resume_after_manual_resolution":
        return bool(explicit_resume)
    return True


def controller_contract_snapshot() -> dict[str, object]:
    return {
        "acceptance_decisions": list(ACCEPTANCE_DECISIONS),
        "post_task_decisions": list(POST_TASK_DECISIONS),
        "resume_modes": list(RESUME_MODES),
        "checkpoint_truth_fields": list(CHECKPOINT_TRUTH_FIELDS),
        "resume_metadata_fields": list(RESUME_METADATA_FIELDS),
        "controller_failure_categories": list(CONTROLLER_FAILURE_CATEGORIES),
        "controller_strict_mode_paths": list(CONTROLLER_STRICT_MODE_PATHS),
        "controller_proof_test_paths": list(CONTROLLER_PROOF_TEST_PATHS),
        "controller_family_files": list(CONTROLLER_FAMILY_FILES),
        "controller_failure_digest_fields": list(CONTROLLER_FAILURE_DIGEST_FIELDS),
        "controller_runtime_delegate_surfaces": list(CONTROLLER_RUNTIME_DELEGATE_SURFACES),
        "role_artifact_envelope_field_names": [
            "coder_artifact_envelope",
            "tester_artifact_envelope",
            "controller_artifact_envelope",
        ],
        "proof_sync_run_task_exports": list(PROOF_SYNC_RUN_TASK_EXPORTS),
        "proof_sync_multi_agent_loop_exports": list(PROOF_SYNC_MULTI_AGENT_LOOP_EXPORTS),
        "proof_sync_compat_result_fields": list(PROOF_SYNC_COMPAT_RESULT_FIELDS),
        "proof_sync_canonical_result_fields": list(PROOF_SYNC_CANONICAL_RESULT_FIELDS),
        "proof_sync_allowed_manifest_entry_keys": list(PROOF_SYNC_ALLOWED_MANIFEST_ENTRY_KEYS),
        "proof_sync_required_boundary_keys": list(PROOF_SYNC_REQUIRED_BOUNDARY_KEYS),
        "proof_sync_required_role_snapshot_keys": list(PROOF_SYNC_REQUIRED_ROLE_SNAPSHOT_KEYS),
        "proof_sync_claim_forbidden_phrases": list(PROOF_SYNC_CLAIM_FORBIDDEN_PHRASES),
        "proof_sync_claim_guard_hints": list(PROOF_SYNC_CLAIM_GUARD_HINTS),
    }


def proof_sync_contract_snapshot() -> dict[str, object]:
    return {
        "run_task_exports": list(PROOF_SYNC_RUN_TASK_EXPORTS),
        "multi_agent_loop_exports": list(PROOF_SYNC_MULTI_AGENT_LOOP_EXPORTS),
        "compatibility_result_fields": list(PROOF_SYNC_COMPAT_RESULT_FIELDS),
        "canonical_result_fields": list(PROOF_SYNC_CANONICAL_RESULT_FIELDS),
        "allowed_manifest_entry_keys": list(PROOF_SYNC_ALLOWED_MANIFEST_ENTRY_KEYS),
        "required_boundary_keys": list(PROOF_SYNC_REQUIRED_BOUNDARY_KEYS),
        "required_role_snapshot_keys": list(PROOF_SYNC_REQUIRED_ROLE_SNAPSHOT_KEYS),
        "claim_forbidden_phrases": list(PROOF_SYNC_CLAIM_FORBIDDEN_PHRASES),
        "claim_guard_hints": list(PROOF_SYNC_CLAIM_GUARD_HINTS),
    }
