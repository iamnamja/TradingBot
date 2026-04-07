from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Literal, Mapping

from agents.lib.controller_contract import canonical_merge_posture_truth, merge_posture_decision_for_flow_stage

Runner = Callable[[list[str], bool], object]
VerificationAuthorityProfile = Literal["local_only", "local_plus_required_ci", "required_ci_only"]

VERIFICATION_AUTHORITY_PROFILES: tuple[VerificationAuthorityProfile, ...] = (
    "local_only",
    "local_plus_required_ci",
    "required_ci_only",
)


@dataclass(frozen=True)
class GitWorkflowResult:
    ok: bool
    step: str
    message: str
    evidence: Dict[str, object] = field(default_factory=dict)



def coerce_verification_authority_profile(
    value: Any,
    default: VerificationAuthorityProfile = "local_only",
) -> VerificationAuthorityProfile:
    text = str(value or "").strip().lower()
    if text in VERIFICATION_AUTHORITY_PROFILES:
        return text  # type: ignore[return-value]
    return default



def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "on", "passed", "pass", "success", "successful"}



def _coerce_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default



def _required_check_state(
    *,
    configured: bool,
    missing: bool,
    pending: bool,
    timed_out: bool,
    failed: bool,
    passed: bool,
) -> str:
    if not configured:
        return "not_configured"
    if missing:
        return "missing"
    if timed_out:
        return "timed_out"
    if failed:
        return "failed"
    if pending:
        return "pending"
    if passed:
        return "passed"
    return "unknown"



def canonical_required_check_truth(
    payload: Mapping[str, Any] | None = None,
    *,
    verification_authority_profile: Any = "local_only",
    required_checks_discovered: Any | None = None,
    required_checks_missing: Any | None = None,
    required_checks_pending: Any | None = None,
    required_checks_timed_out: Any | None = None,
    required_checks_failed: Any | None = None,
    required_checks_passed: Any | None = None,
    missing_required_checks_blocks_merge: Any | None = None,
    hosted_checks_source: Any | None = None,
    hosted_checks_reported: Any | None = None,
) -> dict[str, object]:
    data = payload or {}
    profile = coerce_verification_authority_profile(verification_authority_profile)
    configured = profile != "local_only"
    discovered = _coerce_bool(
        required_checks_discovered if required_checks_discovered is not None else data.get("required_checks_discovered")
    )
    pending = _coerce_bool(required_checks_pending if required_checks_pending is not None else data.get("required_checks_pending"))
    timed_out = _coerce_bool(
        required_checks_timed_out if required_checks_timed_out is not None else data.get("required_checks_timed_out")
    )
    failed = _coerce_bool(required_checks_failed if required_checks_failed is not None else data.get("required_checks_failed"))
    explicit_missing = required_checks_missing if required_checks_missing is not None else data.get("required_checks_missing")
    if explicit_missing is None:
        missing = configured and not discovered and not pending and not timed_out and not failed and not _coerce_bool(
            required_checks_passed if required_checks_passed is not None else data.get("required_checks_passed")
        )
    else:
        missing = _coerce_bool(explicit_missing)
    explicit_passed = required_checks_passed if required_checks_passed is not None else data.get("required_checks_passed")
    if explicit_passed is None:
        passed = not configured
    else:
        passed = _coerce_bool(explicit_passed)
    if missing or pending or timed_out or failed:
        passed = False
    block_missing = _coerce_bool(
        missing_required_checks_blocks_merge
        if missing_required_checks_blocks_merge is not None
        else data.get("missing_required_checks_blocks_merge", configured)
    )
    hosted_source = _coerce_text(
        hosted_checks_source if hosted_checks_source is not None else data.get("hosted_checks_source"),
        default=("not_required" if not configured else "gh_pr_checks"),
    )
    hosted_reported = _coerce_bool(
        hosted_checks_reported if hosted_checks_reported is not None else data.get("hosted_checks_reported", discovered)
    )
    hosted_available = (not configured) or hosted_reported
    hosted_satisfied = (not configured) or (hosted_reported and passed)
    authority_satisfied = hosted_satisfied if configured else True
    return {
        "verification_authority_profile": profile,
        "required_checks_configured": configured,
        "required_checks_discovered": discovered,
        "required_checks_missing": missing,
        "required_checks_pending": pending,
        "required_checks_timed_out": timed_out,
        "required_checks_failed": failed,
        "required_checks_passed": passed,
        "missing_required_checks_blocks_merge": block_missing,
        "verification_authority_satisfied": authority_satisfied,
        "required_check_state": _required_check_state(
            configured=configured,
            missing=missing,
            pending=pending,
            timed_out=timed_out,
            failed=failed,
            passed=passed,
        ),
        "hosted_checks_source": hosted_source,
        "hosted_checks_reported": hosted_reported,
        "hosted_authority_available": hosted_available,
        "hosted_authority_satisfied": hosted_satisfied,
    }


def evaluate_verification_authority(
    *,
    verification_authority_profile: Any,
    local_validation_passed: bool,
    required_check_truth: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    profile = coerce_verification_authority_profile(verification_authority_profile)
    truth = canonical_required_check_truth(required_check_truth, verification_authority_profile=profile)
    local_required = profile != "required_ci_only"
    required_ci_required = profile != "local_only"
    local_satisfied = (not local_required) or bool(local_validation_passed)
    hosted_available = bool(truth["hosted_authority_available"])
    required_ci_satisfied = (not required_ci_required) or bool(truth["hosted_authority_satisfied"])
    satisfied = local_satisfied and required_ci_satisfied
    if satisfied:
        summary = "Configured verification authority is satisfied."
        blocking_reason = ""
        controller_report = {
            "acceptance_decision": "accepted",
            "post_task_decision": "continue",
            "next_task_may_proceed": True,
            "note": summary,
        }
    elif not local_satisfied:
        summary = "Configured verification authority is not satisfied because local validation did not pass."
        blocking_reason = "local_validation_failed"
        controller_report = {
            "acceptance_decision": "retryable_failure",
            "post_task_decision": "stop",
            "next_task_may_proceed": False,
            "note": summary,
        }
    else:
        state = str(truth["required_check_state"])
        if not hosted_available:
            summary = "Configured hosted verification authority is not available because required hosted CI checks were not reported."
            blocking_reason = "hosted_required_checks_not_reported"
        elif state == "missing":
            summary = "Configured verification authority is not satisfied because required CI checks were not discovered."
            blocking_reason = "required_checks_missing"
        elif state == "pending":
            summary = "Configured verification authority is not satisfied because required CI checks are still pending."
            blocking_reason = "required_checks_pending"
        elif state == "timed_out":
            summary = "Configured verification authority is not satisfied because required CI checks timed out."
            blocking_reason = "required_checks_timed_out"
        elif state == "failed":
            summary = "Configured verification authority is not satisfied because required CI checks failed."
            blocking_reason = "required_checks_failed"
        else:
            summary = "Configured verification authority is not satisfied because required CI checks did not report success."
            blocking_reason = "required_checks_unsatisfied"
        controller_report = {
            "acceptance_decision": "blocked",
            "post_task_decision": "stop",
            "next_task_may_proceed": False,
            "note": summary,
        }
    return {
        "verification_authority_profile": profile,
        "local_validation_required": local_required,
        "required_ci_required": required_ci_required,
        "local_validation_satisfied": local_satisfied,
        "required_ci_satisfied": required_ci_satisfied,
        "hosted_authority_available": hosted_available,
        "hosted_authority_satisfied": bool(truth["hosted_authority_satisfied"]),
        "verification_authority_satisfied": satisfied,
        "blocking_reason": blocking_reason,
        "summary": summary,
        "required_check_truth": dict(truth),
        "controller_report": controller_report,
    }


def _extract_stdout_stderr(result: object) -> tuple[str, str]:
    if isinstance(result, Mapping):
        return str(result.get("stdout") or ""), str(result.get("stderr") or "")
    return str(getattr(result, "stdout", "") or ""), str(getattr(result, "stderr", "") or "")



def _infer_required_check_truth_from_output(text: str, *, profile: VerificationAuthorityProfile) -> dict[str, object]:
    lower = text.lower()
    discovered = "no checks reported" not in lower and bool(text.strip())
    missing = False
    pending = False
    timed_out = False
    failed = False
    passed = False

    if not discovered:
        missing = profile != "local_only"
    else:
        if "pending" in lower or "in progress" in lower or "queued" in lower:
            pending = True
        if "timed out" in lower or "timeout" in lower:
            timed_out = True
        if "fail" in lower or "error" in lower or "cancel" in lower:
            failed = True
        if not pending and not timed_out and not failed and (
            "passed" in lower or "successful" in lower or "success" in lower
        ):
            passed = True

    return canonical_required_check_truth(
        verification_authority_profile=profile,
        required_checks_discovered=discovered,
        required_checks_missing=missing,
        required_checks_pending=pending,
        required_checks_timed_out=timed_out,
        required_checks_failed=failed,
        required_checks_passed=passed,
        hosted_checks_source="gh_pr_checks",
        hosted_checks_reported=discovered,
    )



def create_pr(runner: Runner, *, title: str, body: str = "") -> GitWorkflowResult:
    try:
        runner(["gh", "pr", "create", "--fill", "--title", title, "--body", body], True)
    except Exception as exc:
        return GitWorkflowResult(False, "create_pr", f"PR creation failed: {exc}")
    return GitWorkflowResult(True, "create_pr", "PR created")



def wait_for_required_checks(
    runner: Runner,
    *,
    verification_authority_profile: Any = "local_plus_required_ci",
) -> GitWorkflowResult:
    profile = coerce_verification_authority_profile(verification_authority_profile)
    if profile == "local_only":
        evidence = canonical_required_check_truth(verification_authority_profile=profile)
        return GitWorkflowResult(True, "wait_for_required_checks", "required CI checks not configured", evidence=evidence)
    try:
        result = runner(["gh", "pr", "checks", "--watch"], True)
    except Exception as exc:
        evidence = canonical_required_check_truth(
            verification_authority_profile=profile,
            required_checks_discovered=False,
            required_checks_missing=True,
        )
        return GitWorkflowResult(False, "wait_for_required_checks", f"required checks failed: {exc}", evidence=evidence)
    stdout, stderr = _extract_stdout_stderr(result)
    evidence = _infer_required_check_truth_from_output("\n".join([stdout, stderr]).strip(), profile=profile)
    if bool(evidence["verification_authority_satisfied"]):
        return GitWorkflowResult(True, "wait_for_required_checks", "required checks passed", evidence=evidence)
    state = str(evidence["required_check_state"])
    if state == "missing":
        message = "required checks missing"
    elif state == "pending":
        message = "required checks pending"
    elif state == "timed_out":
        message = "required checks timed out"
    elif state == "failed":
        message = "required checks failed"
    else:
        message = "required checks did not report success"
    return GitWorkflowResult(False, "wait_for_required_checks", message, evidence=evidence)



def merge_pr(runner: Runner) -> GitWorkflowResult:
    try:
        runner(["gh", "pr", "merge", "--merge", "--auto", "--delete-branch"], True)
    except Exception as exc:
        return GitWorkflowResult(False, "merge_pr", f"PR merge failed: {exc}")
    return GitWorkflowResult(True, "merge_pr", "PR merged")



def reset_main_clean(runner: Runner) -> GitWorkflowResult:
    try:
        runner(["git", "switch", "main"], True)
        runner(["git", "fetch", "origin"], True)
        runner(["git", "reset", "--hard", "origin/main"], True)
        runner(["git", "clean", "-fd"], True)
    except Exception as exc:
        return GitWorkflowResult(False, "reset_main", f"clean main reset failed: {exc}")
    return GitWorkflowResult(True, "reset_main", "clean main reset complete")



def accepted_task_pr_merge_flow(
    runner: Runner,
    *,
    accepted: bool,
    autonomous_merge_enabled: bool,
    pr_title: str,
    pr_body: str = "",
    verification_authority_profile: Any = "local_plus_required_ci",
) -> Dict[str, object]:
    profile = coerce_verification_authority_profile(verification_authority_profile)
    required_truth = canonical_required_check_truth(verification_authority_profile=profile)
    result: Dict[str, object] = {
        "accepted": bool(accepted),
        "autonomous_merge_enabled": bool(autonomous_merge_enabled),
        "verification_authority_profile": profile,
        "stopped_honestly": False,
        "stop_reason": "",
        "post_task_decision": "continue",
        "created_pr": False,
        "required_checks_passed": bool(required_truth["required_checks_passed"]),
        "merged": False,
        "main_reset_clean": False,
        "accepted_task_pr_flow_completed": False,
        "merged_to_main": False,
        "clean_main_reset_completed": False,
        "next_task_may_proceed": False,
        **required_truth,
    }

    if not accepted:
        result["stop_reason"] = "task not accepted; PR flow skipped"
        result["post_task_decision"] = "stop"
        result.update(canonical_merge_posture_truth(result))
        return result

    if not autonomous_merge_enabled:
        result["stop_reason"] = "autonomous merge disabled by operator control"
        result["post_task_decision"] = "stop"
        result.update(canonical_merge_posture_truth(result))
        return result

    created = create_pr(runner, title=pr_title, body=pr_body)
    if not created.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = created.message
        result["post_task_decision"] = merge_posture_decision_for_flow_stage("merge")
        result.update(canonical_merge_posture_truth(result))
        return result
    result["created_pr"] = True

    checks = wait_for_required_checks(runner, verification_authority_profile=profile)
    result.update(dict(checks.evidence or {}))
    result["required_checks_passed"] = bool(result.get("required_checks_passed", False))
    if not checks.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = checks.message
        result["post_task_decision"] = merge_posture_decision_for_flow_stage("checks")
        result.update(canonical_merge_posture_truth(result))
        return result

    merged = merge_pr(runner)
    if not merged.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = merged.message
        result["post_task_decision"] = merge_posture_decision_for_flow_stage("merge")
        result.update(canonical_merge_posture_truth(result))
        return result
    result["merged"] = True
    result["merged_to_main"] = True

    reset = reset_main_clean(runner)
    if not reset.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = reset.message
        result["post_task_decision"] = merge_posture_decision_for_flow_stage("reset")
        result.update(canonical_merge_posture_truth(result))
        return result
    result["main_reset_clean"] = True
    result["clean_main_reset_completed"] = True
    result.update(
        canonical_merge_posture_truth(
            required_checks_passed=result["required_checks_passed"],
            merged_to_main=result["merged_to_main"],
            clean_main_reset_completed=result["clean_main_reset_completed"],
        )
    )
    result["next_task_may_proceed"] = True
    return result



def report_branch_push_ready(branch: str, *, printer=print) -> None:
    printer(f"Pushed branch: {branch}")
    printer("Create a PR on GitHub for this branch (repo rules require PR).")
