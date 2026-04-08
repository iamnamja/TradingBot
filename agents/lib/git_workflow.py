from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Literal, Mapping, Sequence

from agents.lib.controller_contract import canonical_merge_posture_truth, merge_posture_decision_for_flow_stage

Runner = Callable[[list[str], bool], object]
VerificationAuthorityProfile = Literal["local_only", "local_plus_required_ci", "required_ci_only"]

VERIFICATION_AUTHORITY_PROFILES: tuple[VerificationAuthorityProfile, ...] = (
    "local_only",
    "local_plus_required_ci",
    "required_ci_only",
)
DEFAULT_REPO_REQUIRED_CHECKS: tuple[str, ...] = ()
DEFAULT_REPO_CHECK_CONTRACT_SOURCE = "repo_defaults"
DEFAULT_HOSTED_CHECKS_SOURCE = "gh_pr_checks"
DEFAULT_REPO_DEFAULT_BRANCH = "main"
DEFAULT_ENFORCEMENT_PROBE_STRATEGY = "rules_branch_then_branch_protection"


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


def _coerce_required_check_names(value: Any) -> tuple[str, ...]:
    if value is None:
        raw_values: Sequence[object] = DEFAULT_REPO_REQUIRED_CHECKS
    elif isinstance(value, str):
        raw_values = [value]
    elif isinstance(value, Mapping):
        raw_values = list(value.keys())
    else:
        raw_values = list(value)
    normalized = sorted({str(item).strip() for item in raw_values if str(item).strip()})
    return tuple(normalized)


def canonical_repo_check_contract(
    payload: Mapping[str, Any] | None = None,
    *,
    required_checks: Any | None = None,
    repo_check_contract_source: Any | None = None,
    missing_required_checks_blocks_merge: Any | None = None,
    hosted_checks_source: Any | None = None,
    repo_default_branch: Any | None = None,
    enforcement_probe_strategy: Any | None = None,
) -> dict[str, object]:
    data = payload or {}
    names = _coerce_required_check_names(
        required_checks
        if required_checks is not None
        else data.get("required_checks", data.get("repo_required_checks", DEFAULT_REPO_REQUIRED_CHECKS))
    )
    configured = bool(names)
    source = _coerce_text(
        repo_check_contract_source
        if repo_check_contract_source is not None
        else data.get("repo_check_contract_source"),
        default=DEFAULT_REPO_CHECK_CONTRACT_SOURCE,
    )
    block_missing = _coerce_bool(
        missing_required_checks_blocks_merge
        if missing_required_checks_blocks_merge is not None
        else data.get("missing_required_checks_blocks_merge", True)
    )
    hosted_source = _coerce_text(
        hosted_checks_source if hosted_checks_source is not None else data.get("hosted_checks_source"),
        default=DEFAULT_HOSTED_CHECKS_SOURCE,
    )
    default_branch = _coerce_text(
        repo_default_branch if repo_default_branch is not None else data.get("repo_default_branch"),
        default=DEFAULT_REPO_DEFAULT_BRANCH,
    )
    probe_strategy = _coerce_text(
        enforcement_probe_strategy if enforcement_probe_strategy is not None else data.get("enforcement_probe_strategy"),
        default=DEFAULT_ENFORCEMENT_PROBE_STRATEGY,
    )
    if configured:
        note = f"Repo check contract requires hosted checks: {', '.join(names)}."
    else:
        note = "Repo check contract does not declare required hosted checks."
    return {
        "repo_check_contract_source": source,
        "repo_required_checks": names,
        "repo_check_contract_configured": configured,
        "missing_required_checks_blocks_merge": block_missing,
        "hosted_checks_source": hosted_source,
        "repo_default_branch": default_branch,
        "enforcement_probe_strategy": probe_strategy,
        "repo_check_contract_note": note,
    }


def _parse_json_payload(text: str) -> Any | None:
    payload_text = str(text or "").strip()
    if not payload_text:
        return None
    try:
        return json.loads(payload_text)
    except Exception:
        return None


def _merge_required_check_contexts(*values: Any) -> tuple[str, ...]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _coerce_required_check_names(value):
            if item not in seen:
                merged.append(item)
                seen.add(item)
    return tuple(merged)


def _parse_branch_rules_required_check_payload(payload: Any) -> dict[str, object]:
    rules = payload if isinstance(payload, list) else []
    required_contexts: list[str] = []
    ruleset_ids: list[str] = []
    ruleset_sources: list[str] = []
    strict_policy = False
    required_rule_present = False

    for rule in rules:
        if not isinstance(rule, Mapping):
            continue
        if str(rule.get("type") or "").strip() != "required_status_checks":
            continue
        required_rule_present = True
        parameters = rule.get("parameters") if isinstance(rule.get("parameters"), Mapping) else {}
        strict_policy = strict_policy or _coerce_bool(parameters.get("strict_required_status_checks_policy"))
        required_contexts = list(
            _merge_required_check_contexts(
                required_contexts,
                [item.get("context") if isinstance(item, Mapping) else item for item in list(parameters.get("required_status_checks", []))],
            )
        )
        ruleset_id = str(rule.get("ruleset_id") or "").strip()
        ruleset_source = str(rule.get("ruleset_source") or rule.get("ruleset_source_type") or "").strip()
        if ruleset_id and ruleset_id not in ruleset_ids:
            ruleset_ids.append(ruleset_id)
        if ruleset_source and ruleset_source not in ruleset_sources:
            ruleset_sources.append(ruleset_source)

    return {
        "branch_rules_checked": isinstance(payload, list),
        "required_status_checks_rule_present": required_rule_present,
        "required_status_check_contexts": tuple(required_contexts),
        "strict_required_status_checks_policy": strict_policy,
        "ruleset_ids": tuple(ruleset_ids),
        "ruleset_sources": tuple(ruleset_sources),
    }


def _parse_branch_protection_required_check_payload(payload: Any) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        return {
            "branch_protection_enabled": False,
            "required_status_checks_rule_present": False,
            "required_status_check_contexts": (),
            "strict_required_status_checks_policy": False,
        }

    required_status_checks = payload.get("required_status_checks")
    if not isinstance(required_status_checks, Mapping):
        return {
            "branch_protection_enabled": bool(payload),
            "required_status_checks_rule_present": False,
            "required_status_check_contexts": (),
            "strict_required_status_checks_policy": False,
        }

    contexts = _merge_required_check_contexts(
        required_status_checks.get("contexts"),
        [item.get("context") if isinstance(item, Mapping) else item for item in list(required_status_checks.get("checks", []))],
    )
    return {
        "branch_protection_enabled": True,
        "required_status_checks_rule_present": True,
        "required_status_check_contexts": contexts,
        "strict_required_status_checks_policy": _coerce_bool(required_status_checks.get("strict")),
    }


def canonical_repo_enforcement_truth(
    payload: Mapping[str, Any] | None = None,
    *,
    repo_check_contract: Mapping[str, Any] | None = None,
    enforcement_probe_available: Any | None = None,
    enforcement_probe_status: Any | None = None,
    enforcement_source: Any | None = None,
    enforcement_note: Any | None = None,
    branch_rules_checked: Any | None = None,
    branch_protection_enabled: Any | None = None,
    required_status_checks_rule_present: Any | None = None,
    required_status_check_contexts: Any | None = None,
    strict_required_status_checks_policy: Any | None = None,
    ruleset_ids: Any | None = None,
    ruleset_sources: Any | None = None,
) -> dict[str, object]:
    data = payload or {}
    contract = canonical_repo_check_contract(repo_check_contract if repo_check_contract is not None else data.get("repo_check_contract"))
    expected_checks = tuple(contract["repo_required_checks"])
    enforced_contexts = _coerce_required_check_names(
        required_status_check_contexts
        if required_status_check_contexts is not None
        else data.get("required_status_check_contexts")
    )
    probe_available = _coerce_bool(
        enforcement_probe_available
        if enforcement_probe_available is not None
        else data.get("enforcement_probe_available", True)
    )
    probe_status = _coerce_text(
        enforcement_probe_status if enforcement_probe_status is not None else data.get("enforcement_probe_status"),
        default=("not_required" if not expected_checks else ""),
    )
    source = _coerce_text(
        enforcement_source if enforcement_source is not None else data.get("enforcement_source"),
        default="",
    )
    note = _coerce_text(enforcement_note if enforcement_note is not None else data.get("enforcement_note"), default="")
    rules_checked = _coerce_bool(
        branch_rules_checked if branch_rules_checked is not None else data.get("branch_rules_checked", False)
    )
    protection_enabled = _coerce_bool(
        branch_protection_enabled if branch_protection_enabled is not None else data.get("branch_protection_enabled", False)
    )
    rule_present = _coerce_bool(
        required_status_checks_rule_present
        if required_status_checks_rule_present is not None
        else data.get("required_status_checks_rule_present", bool(enforced_contexts))
    )
    strict_policy = _coerce_bool(
        strict_required_status_checks_policy
        if strict_required_status_checks_policy is not None
        else data.get("strict_required_status_checks_policy", False)
    )
    ruleset_id_values = _coerce_required_check_names(ruleset_ids if ruleset_ids is not None else data.get("ruleset_ids"))
    ruleset_source_values = _coerce_required_check_names(
        ruleset_sources if ruleset_sources is not None else data.get("ruleset_sources")
    )
    missing_contexts = tuple(check for check in expected_checks if check not in enforced_contexts)
    converged = False

    if not expected_checks:
        probe_status = probe_status or "not_required"
        note = note or "Repo check contract does not require hosted check enforcement."
        converged = True
    elif not probe_available:
        probe_status = probe_status or "unavailable"
        note = note or "GitHub required-check enforcement probe could not be executed."
    elif not rule_present:
        probe_status = probe_status or "required_status_check_rule_missing"
        note = note or "GitHub branch rules/protection do not require the expected status-check contexts."
    elif missing_contexts:
        probe_status = probe_status or "required_check_context_missing"
        note = note or f"GitHub enforcement is missing required status-check contexts: {', '.join(missing_contexts)}."
    else:
        probe_status = probe_status or "satisfied"
        note = note or "GitHub branch rules/protection require the expected status-check contexts."
        converged = True

    return {
        "repo_check_contract": dict(contract),
        "repo_required_checks": expected_checks,
        "repo_default_branch": str(contract["repo_default_branch"]),
        "enforcement_probe_strategy": str(contract["enforcement_probe_strategy"]),
        "enforcement_probe_available": probe_available,
        "enforcement_probe_status": probe_status,
        "enforcement_source": source,
        "enforcement_note": note,
        "branch_rules_checked": rules_checked,
        "branch_protection_enabled": protection_enabled,
        "required_status_checks_rule_present": rule_present,
        "required_status_check_contexts": enforced_contexts,
        "missing_required_check_contexts": missing_contexts,
        "strict_required_status_checks_policy": strict_policy,
        "ruleset_ids": ruleset_id_values,
        "ruleset_sources": ruleset_source_values,
        "repo_required_check_enforcement_converged": converged,
    }


def _stdout_and_stderr_text(result: object) -> str:
    stdout, stderr = _extract_stdout_stderr(result)
    return "\n".join(part for part in (stdout, stderr) if str(part).strip()).strip()


def _classify_probe_error(exc: Exception) -> str:
    message = str(exc or "").lower()
    if "404" in message or "not found" in message or "not protected" in message:
        return "missing"
    return "unavailable"


def probe_repo_required_check_enforcement(
    runner: Runner,
    *,
    repo_check_contract: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    contract = canonical_repo_check_contract(repo_check_contract)
    if not bool(contract["repo_check_contract_configured"]):
        return canonical_repo_enforcement_truth(repo_check_contract=contract)

    branch = str(contract["repo_default_branch"])
    rules_error: Exception | None = None

    try:
        rules_result = runner(["gh", "api", f"repos/{{owner}}/{{repo}}/rules/branches/{branch}"], True)
        rules_payload = _parse_json_payload(_stdout_and_stderr_text(rules_result))
        rules_truth = _parse_branch_rules_required_check_payload(rules_payload)
        if bool(rules_truth["required_status_checks_rule_present"]):
            return canonical_repo_enforcement_truth(
                repo_check_contract=contract,
                enforcement_probe_available=True,
                enforcement_probe_status="satisfied",
                enforcement_source="github_branch_rules",
                enforcement_note="GitHub branch rules are enforcing the configured required status-check contexts."
                if not tuple(check for check in contract["repo_required_checks"] if check not in tuple(rules_truth["required_status_check_contexts"]))
                else "",
                **rules_truth,
            )
    except Exception as exc:
        rules_error = exc

    try:
        protection_result = runner(["gh", "api", f"repos/{{owner}}/{{repo}}/branches/{branch}/protection"], True)
        protection_payload = _parse_json_payload(_stdout_and_stderr_text(protection_result))
        protection_truth = _parse_branch_protection_required_check_payload(protection_payload)
        return canonical_repo_enforcement_truth(
            repo_check_contract=contract,
            enforcement_probe_available=True,
            enforcement_probe_status=(
                "required_status_check_rule_missing"
                if not bool(protection_truth["required_status_checks_rule_present"])
                else ""
            ),
            enforcement_source="github_branch_protection",
            enforcement_note=(
                "GitHub branch protection is active but does not require the configured status-check contexts."
                if not bool(protection_truth["required_status_checks_rule_present"])
                else ""
            ),
            **protection_truth,
        )
    except Exception as exc:
        classification = _classify_probe_error(exc)
        if classification == "missing":
            return canonical_repo_enforcement_truth(
                repo_check_contract=contract,
                enforcement_probe_available=True,
                enforcement_probe_status="required_status_check_rule_missing",
                enforcement_source="github_branch_protection",
                enforcement_note="GitHub branch protection is not configured for the target base branch.",
            )
        note_parts = []
        if rules_error is not None:
            note_parts.append(str(rules_error))
        note_parts.append(str(exc))
        return canonical_repo_enforcement_truth(
            repo_check_contract=contract,
            enforcement_probe_available=False,
            enforcement_probe_status="unavailable",
            enforcement_source="github_branch_rules_or_protection",
            enforcement_note="; ".join(part for part in note_parts if part),
        )


def evaluate_repo_required_check_convergence(
    *,
    repo_check_contract: Mapping[str, Any] | None = None,
    repo_enforcement_truth: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    contract = canonical_repo_check_contract(repo_check_contract)
    truth = canonical_repo_enforcement_truth(
        repo_enforcement_truth,
        repo_check_contract=contract,
    )
    if not bool(contract["repo_check_contract_configured"]):
        reason = "repo_check_contract_not_configured"
        summary = "Repo check contract is not configured, so GitHub required-check enforcement is not applicable."
        converged = False
    elif not bool(truth["enforcement_probe_available"]):
        reason = "enforcement_probe_unavailable"
        summary = "GitHub required-check enforcement could not be probed."
        converged = False
    elif not bool(truth["required_status_checks_rule_present"]):
        reason = "required_status_check_rule_missing"
        summary = "GitHub branch rules/protection do not require the configured status-check contexts."
        converged = False
    elif bool(truth["missing_required_check_contexts"]):
        reason = "required_check_context_missing"
        summary = "GitHub enforcement is missing at least one required status-check context from the repo contract."
        converged = False
    else:
        reason = "converged"
        summary = "GitHub branch rules/protection require the configured status-check contexts."
        converged = True
    return {
        "repo_check_contract": dict(contract),
        "repo_enforcement_truth": dict(truth),
        "repo_required_check_enforcement_converged": converged,
        "repo_required_check_enforcement_reason": reason,
        "summary": summary,
    }


def _required_check_state(
    *,
    configured: bool,
    unavailable: bool,
    misconfigured: bool,
    missing: bool,
    pending: bool,
    timed_out: bool,
    failed: bool,
    passed: bool,
) -> str:
    if not configured:
        return "not_required"
    if unavailable:
        return "unavailable"
    if misconfigured:
        return "misconfigured"
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
    repo_check_contract: Mapping[str, Any] | None = None,
    repo_required_checks: Any | None = None,
    repo_check_contract_source: Any | None = None,
    required_checks_discovered: Any | None = None,
    required_checks_missing: Any | None = None,
    required_checks_pending: Any | None = None,
    required_checks_timed_out: Any | None = None,
    required_checks_failed: Any | None = None,
    required_checks_passed: Any | None = None,
    missing_required_checks_blocks_merge: Any | None = None,
    hosted_checks_source: Any | None = None,
    hosted_checks_reported: Any | None = None,
    hosted_authority_probe_status: Any | None = None,
    hosted_authority_probe_note: Any | None = None,
) -> dict[str, object]:
    data = payload or {}
    profile = coerce_verification_authority_profile(verification_authority_profile)
    hosted_required = profile != "local_only"
    contract = canonical_repo_check_contract(
        repo_check_contract if repo_check_contract is not None else data.get("repo_check_contract"),
        required_checks=repo_required_checks if repo_required_checks is not None else data.get("repo_required_checks"),
        repo_check_contract_source=(
            repo_check_contract_source if repo_check_contract_source is not None else data.get("repo_check_contract_source")
        ),
        missing_required_checks_blocks_merge=(
            missing_required_checks_blocks_merge
            if missing_required_checks_blocks_merge is not None
            else data.get("missing_required_checks_blocks_merge")
        ),
        hosted_checks_source=hosted_checks_source if hosted_checks_source is not None else data.get("hosted_checks_source"),
        repo_default_branch=data.get("repo_default_branch"),
        enforcement_probe_strategy=data.get("enforcement_probe_strategy"),
    )
    contract_configured = bool(contract["repo_check_contract_configured"])
    discovered = _coerce_bool(
        required_checks_discovered if required_checks_discovered is not None else data.get("required_checks_discovered")
    )
    pending = _coerce_bool(required_checks_pending if required_checks_pending is not None else data.get("required_checks_pending"))
    timed_out = _coerce_bool(
        required_checks_timed_out if required_checks_timed_out is not None else data.get("required_checks_timed_out")
    )
    failed = _coerce_bool(required_checks_failed if required_checks_failed is not None else data.get("required_checks_failed"))
    explicit_missing = required_checks_missing if required_checks_missing is not None else data.get("required_checks_missing")
    explicit_passed = required_checks_passed if required_checks_passed is not None else data.get("required_checks_passed")
    hosted_reported = _coerce_bool(
        hosted_checks_reported if hosted_checks_reported is not None else data.get("hosted_checks_reported", discovered)
    )
    probe_status = _coerce_text(
        hosted_authority_probe_status if hosted_authority_probe_status is not None else data.get("hosted_authority_probe_status")
    )
    probe_note = _coerce_text(
        hosted_authority_probe_note if hosted_authority_probe_note is not None else data.get("hosted_authority_probe_note")
    )

    unavailable = False
    misconfigured = False
    missing = False
    passed = False

    if not hosted_required:
        passed = True
        probe_status = "not_required"
        probe_note = probe_note or "Hosted authority is not required for the configured local-only verification profile."
    else:
        if probe_status == "unavailable":
            unavailable = True
            probe_note = probe_note or "Hosted authority probe could not be executed."
        elif not contract_configured:
            misconfigured = True
            probe_status = "misconfigured"
            probe_note = probe_note or str(contract["repo_check_contract_note"])
        elif not hosted_reported or not discovered:
            misconfigured = True
            probe_status = "misconfigured"
            missing = _coerce_bool(explicit_missing) if explicit_missing is not None else False
            probe_note = probe_note or "Hosted checks did not report on the branch."
        else:
            if explicit_missing is None:
                missing = False
            else:
                missing = _coerce_bool(explicit_missing)
            if explicit_passed is None:
                passed = not pending and not timed_out and not failed and not missing
            else:
                passed = _coerce_bool(explicit_passed)
            if missing or pending or timed_out or failed:
                passed = False
            if passed:
                probe_status = "satisfied"
                probe_note = probe_note or "Hosted authority probe reported the required checks as satisfied."
            else:
                probe_status = probe_status or "reported_unsatisfied"
                if pending:
                    probe_note = probe_note or "Hosted authority probe reported pending required checks."
                elif timed_out:
                    probe_note = probe_note or "Hosted authority probe reported timed-out required checks."
                elif failed:
                    probe_note = probe_note or "Hosted authority probe reported failed required checks."
                elif missing:
                    probe_note = probe_note or "Hosted authority probe reported missing required checks."
                else:
                    probe_note = probe_note or "Hosted authority probe reported checks but did not confirm success."

    if unavailable or misconfigured:
        pending = False
        timed_out = False
        failed = False
        passed = False

    hosted_available = (not hosted_required) or probe_status not in {"unavailable", "misconfigured"}
    hosted_satisfied = (not hosted_required) or probe_status == "satisfied"
    authority_satisfied = (not hosted_required) or hosted_satisfied

    return {
        "verification_authority_profile": profile,
        "required_checks_configured": hosted_required,
        "repo_check_contract_source": str(contract["repo_check_contract_source"]),
        "repo_required_checks": tuple(contract["repo_required_checks"]),
        "repo_check_contract_configured": contract_configured,
        "repo_check_contract_note": str(contract["repo_check_contract_note"]),
        "required_checks_discovered": discovered,
        "required_checks_missing": missing,
        "required_checks_pending": pending,
        "required_checks_timed_out": timed_out,
        "required_checks_failed": failed,
        "required_checks_passed": passed,
        "required_checks_unavailable": unavailable,
        "required_checks_misconfigured": misconfigured,
        "missing_required_checks_blocks_merge": bool(contract["missing_required_checks_blocks_merge"]),
        "verification_authority_satisfied": authority_satisfied,
        "required_check_state": _required_check_state(
            configured=hosted_required,
            unavailable=unavailable,
            misconfigured=misconfigured,
            missing=missing,
            pending=pending,
            timed_out=timed_out,
            failed=failed,
            passed=passed,
        ),
        "hosted_checks_source": str(contract["hosted_checks_source"]),
        "hosted_checks_reported": hosted_reported,
        "hosted_authority_available": hosted_available,
        "hosted_authority_satisfied": hosted_satisfied,
        "hosted_authority_probe_status": probe_status or ("not_required" if not hosted_required else "reported_unsatisfied"),
        "hosted_authority_probe_note": probe_note,
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
        probe_status = str(truth["hosted_authority_probe_status"])
        if probe_status == "unavailable":
            summary = "Configured hosted verification authority is not available because the hosted check probe could not be executed."
            blocking_reason = "hosted_probe_unavailable"
        elif probe_status == "misconfigured":
            summary = "Configured hosted verification authority is not satisfied because the repo check contract or branch reporting is misconfigured."
            blocking_reason = "hosted_required_checks_misconfigured"
        else:
            state = str(truth["required_check_state"])
            if state == "pending":
                summary = "Configured verification authority is not satisfied because required CI checks are still pending."
                blocking_reason = "required_checks_pending"
            elif state == "timed_out":
                summary = "Configured verification authority is not satisfied because required CI checks timed out."
                blocking_reason = "required_checks_timed_out"
            elif state == "failed":
                summary = "Configured verification authority is not satisfied because required CI checks failed."
                blocking_reason = "required_checks_failed"
            elif state == "missing":
                summary = "Configured verification authority is not satisfied because required CI checks were reported as missing."
                blocking_reason = "required_checks_missing"
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


def _infer_required_check_truth_from_output(
    text: str,
    *,
    profile: VerificationAuthorityProfile,
    repo_check_contract: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    lower = text.lower()
    discovered = "no checks reported" not in lower and bool(text.strip())
    pending = False
    timed_out = False
    failed = False
    passed = False

    if discovered:
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
        repo_check_contract=repo_check_contract,
        required_checks_discovered=discovered,
        required_checks_pending=pending,
        required_checks_timed_out=timed_out,
        required_checks_failed=failed,
        required_checks_passed=passed,
        hosted_checks_reported=discovered,
        hosted_authority_probe_status=("misconfigured" if not discovered else None),
        hosted_authority_probe_note=("Hosted checks did not report on the branch." if not discovered else ""),
    )


def probe_hosted_authority(
    runner: Runner,
    *,
    verification_authority_profile: Any = "local_plus_required_ci",
    repo_check_contract: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    profile = coerce_verification_authority_profile(verification_authority_profile)
    if profile == "local_only":
        return canonical_required_check_truth(
            verification_authority_profile=profile,
            repo_check_contract=repo_check_contract,
        )
    try:
        result = runner(["gh", "pr", "checks", "--watch"], True)
    except Exception as exc:
        return canonical_required_check_truth(
            verification_authority_profile=profile,
            repo_check_contract=repo_check_contract,
            required_checks_discovered=False,
            hosted_checks_reported=False,
            hosted_authority_probe_status="unavailable",
            hosted_authority_probe_note=str(exc),
        )
    stdout, stderr = _extract_stdout_stderr(result)
    return _infer_required_check_truth_from_output(
        "\n".join([stdout, stderr]).strip(),
        profile=profile,
        repo_check_contract=repo_check_contract,
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
    repo_check_contract: Mapping[str, Any] | None = None,
) -> GitWorkflowResult:
    profile = coerce_verification_authority_profile(verification_authority_profile)
    evidence = probe_hosted_authority(
        runner,
        verification_authority_profile=profile,
        repo_check_contract=repo_check_contract,
    )
    if profile == "local_only":
        return GitWorkflowResult(True, "wait_for_required_checks", "required CI checks not configured", evidence=evidence)
    if bool(evidence["verification_authority_satisfied"]):
        return GitWorkflowResult(True, "wait_for_required_checks", "required checks passed", evidence=evidence)

    probe_status = str(evidence["hosted_authority_probe_status"])
    state = str(evidence["required_check_state"])
    if probe_status == "unavailable":
        message = "hosted authority probe unavailable"
    elif probe_status == "misconfigured":
        message = "required checks misconfigured"
    elif state == "missing":
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
    repo_check_contract: Mapping[str, Any] | None = None,
    project_contract: Mapping[str, Any] | None = None,
) -> Dict[str, object]:
    if project_contract is not None and repo_check_contract is None:
        repo_check_contract = project_repo_check_contract(project_contract)
    if project_contract is not None and verification_authority_profile == "local_plus_required_ci":
        verification_authority_profile = project_verification_authority_profile(project_contract)
    profile = coerce_verification_authority_profile(verification_authority_profile)
    repo_contract = canonical_repo_check_contract(repo_check_contract)
    required_truth = canonical_required_check_truth(
        verification_authority_profile=profile,
        repo_check_contract=repo_contract,
    )
    operational = evaluate_hosted_authority_operational_convergence(
        verification_authority_profile=profile,
        repo_check_contract=repo_contract,
        required_check_truth=required_truth,
    )
    repo_enforcement_truth = canonical_repo_enforcement_truth(repo_check_contract=repo_contract)
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
        "unattended_execution_ready": bool(operational["unattended_execution_ready"]),
        "operational_convergence_ready": bool(operational["operational_convergence_ready"]),
        "operational_convergence_reason": str(operational["operational_convergence_reason"]),
        "hosted_authority_operational_convergence": dict(operational),
        "repo_required_check_enforcement": dict(evaluate_repo_required_check_convergence(repo_check_contract=repo_contract, repo_enforcement_truth=repo_enforcement_truth)),
        **required_truth,
        'project_id': str((project_contract or {}).get('project_id', '')),
        'repo_check_contract': dict(repo_contract),
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

    checks = wait_for_required_checks(
        runner,
        verification_authority_profile=profile,
        repo_check_contract=repo_check_contract,
    )
    result.update(dict(checks.evidence or {}))
    result["required_checks_passed"] = bool(result.get("required_checks_passed", False))
    operational = evaluate_hosted_authority_operational_convergence(
        verification_authority_profile=profile,
        repo_check_contract=repo_contract,
        required_check_truth=result,
    )
    result["unattended_execution_ready"] = bool(operational["unattended_execution_ready"])
    result["operational_convergence_ready"] = bool(operational["operational_convergence_ready"])
    result["operational_convergence_reason"] = str(operational["operational_convergence_reason"])
    result["hosted_authority_operational_convergence"] = dict(operational)
    if not checks.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = checks.message
        result["post_task_decision"] = merge_posture_decision_for_flow_stage("checks")
        result.update(canonical_merge_posture_truth(result))
        return result

    repo_enforcement_truth = probe_repo_required_check_enforcement(runner, repo_check_contract=repo_contract)
    result["repo_required_check_enforcement"] = dict(
        evaluate_repo_required_check_convergence(
            repo_check_contract=repo_contract,
            repo_enforcement_truth=repo_enforcement_truth,
        )
    )
    operational = evaluate_hosted_authority_operational_convergence(
        verification_authority_profile=profile,
        repo_check_contract=repo_contract,
        required_check_truth=result,
        repo_enforcement_truth=repo_enforcement_truth,
    )
    result["unattended_execution_ready"] = bool(operational["unattended_execution_ready"])
    result["operational_convergence_ready"] = bool(operational["operational_convergence_ready"])
    result["operational_convergence_reason"] = str(operational["operational_convergence_reason"])
    result["hosted_authority_operational_convergence"] = dict(operational)
    if not bool(result.get("operational_convergence_ready", False)):
        result["stopped_honestly"] = True
        result["stop_reason"] = str(result.get("operational_convergence_reason") or "required check enforcement not converged")
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



def probe_repo_required_check_enforcement_result(
    runner: Runner,
    *,
    repo_check_contract: Mapping[str, Any] | None = None,
) -> GitWorkflowResult:
    evidence = probe_repo_required_check_enforcement(runner, repo_check_contract=repo_check_contract)
    ok = bool(evidence.get("repo_required_check_enforcement_converged", False))
    message = "required-check enforcement converged" if ok else str(evidence.get("enforcement_probe_status") or "required-check enforcement not converged")
    return GitWorkflowResult(ok, "probe_repo_required_check_enforcement", message, evidence=dict(evidence))


def report_branch_push_ready(branch: str, *, printer=print) -> None:
    printer(f"Pushed branch: {branch}")
    printer("Create a PR on GitHub for this branch (repo rules require PR).")



def evaluate_hosted_authority_convergence(
    *,
    verification_authority_profile: Any,
    repo_check_contract: Mapping[str, Any] | None = None,
    required_check_truth: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    profile = coerce_verification_authority_profile(verification_authority_profile)
    contract = canonical_repo_check_contract(repo_check_contract)
    truth = canonical_required_check_truth(
        required_check_truth,
        verification_authority_profile=profile,
        repo_check_contract=contract,
    )
    hosted_required = profile != 'local_only'
    configured = bool(contract['repo_check_contract_configured'])
    expected_checks = tuple(contract['repo_required_checks'])
    reported_checks = tuple(truth['repo_required_checks'])
    contract_match = expected_checks == reported_checks
    probe_status = str(truth['hosted_authority_probe_status'])
    if not hosted_required:
        converged = True
        reason = 'hosted_authority_not_required'
    elif not configured:
        converged = False
        reason = 'repo_check_contract_not_configured'
    elif not contract_match:
        converged = False
        reason = 'repo_check_contract_mismatch'
    elif probe_status in {'unavailable', 'misconfigured'}:
        converged = False
        reason = probe_status
    else:
        converged = True
        reason = 'converged'
    return {
        'verification_authority_profile': profile,
        'repo_check_contract': dict(contract),
        'required_check_truth': dict(truth),
        'hosted_authority_converged': converged,
        'hosted_authority_convergence_reason': reason,
        'hosted_authority_required': hosted_required,
    }


def evaluate_hosted_authority_operational_convergence(
    *,
    verification_authority_profile: Any,
    repo_check_contract: Mapping[str, Any] | None = None,
    required_check_truth: Mapping[str, Any] | None = None,
    repo_enforcement_truth: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    profile = coerce_verification_authority_profile(verification_authority_profile)
    contract = canonical_repo_check_contract(repo_check_contract)
    truth = canonical_required_check_truth(
        required_check_truth,
        verification_authority_profile=profile,
        repo_check_contract=contract,
    )
    enforcement = (
        evaluate_repo_required_check_convergence(
            repo_check_contract=contract,
            repo_enforcement_truth=repo_enforcement_truth,
        )
        if repo_enforcement_truth is not None
        else {
            "repo_check_contract": dict(contract),
            "repo_enforcement_truth": {},
            "repo_required_check_enforcement_converged": None,
            "repo_required_check_enforcement_reason": "not_probed",
            "summary": "GitHub required-check enforcement was not probed in this evaluation.",
        }
    )
    hosted_required = profile != 'local_only'
    discovered = bool(truth['required_checks_discovered'])
    hosted_reported = bool(truth['hosted_checks_reported'])
    probe_status = str(truth['hosted_authority_probe_status'])
    state = str(truth['required_check_state'])
    enforcement_truth = dict(enforcement.get('repo_enforcement_truth') or {})

    if not hosted_required:
        ready = True
        reason = 'hosted_authority_not_required'
        summary = 'Hosted authority is not required, so unattended readiness is not blocked by GitHub check reporting.'
    elif not bool(contract['repo_check_contract_configured']):
        ready = False
        reason = 'repo_check_contract_not_configured'
        summary = 'Repo check contract is not configured, so unattended GitHub readiness is not established.'
    elif repo_enforcement_truth is not None and not bool(enforcement['repo_required_check_enforcement_converged']):
        enforcement_reason = str(enforcement['repo_required_check_enforcement_reason'])
        if enforcement_reason == 'enforcement_probe_unavailable':
            reason = 'required_check_enforcement_probe_unavailable'
            summary = 'GitHub required-check enforcement could not be verified, so unattended readiness is not established.'
        elif enforcement_reason == 'required_status_check_rule_missing':
            reason = 'required_check_enforcement_missing'
            summary = 'GitHub branch rules/protection are not enforcing the configured required status-check contexts, so unattended readiness is not established.'
        elif enforcement_reason == 'required_check_context_missing':
            reason = 'required_check_enforcement_context_mismatch'
            summary = 'GitHub branch rules/protection do not require the same status-check contexts as the repo contract, so unattended readiness is not established.'
        else:
            reason = 'required_check_enforcement_not_converged'
            summary = str(enforcement.get('summary') or 'GitHub required-check enforcement is not yet converged.')
        ready = False
    elif not discovered or not hosted_reported:
        ready = False
        reason = 'hosted_checks_not_reporting'
        summary = 'Hosted checks are not reporting on the branch, so unattended GitHub readiness is not established.'
    elif probe_status == 'unavailable':
        ready = False
        reason = 'hosted_authority_probe_unavailable'
        summary = 'Hosted authority could not be probed, so unattended GitHub readiness is not established.'
    elif probe_status == 'misconfigured':
        ready = False
        reason = 'hosted_checks_misconfigured'
        summary = 'Hosted required checks are misconfigured, so unattended GitHub readiness is not established.'
    elif state != 'passed' or not bool(truth['required_checks_passed']):
        ready = False
        reason = 'required_checks_not_green'
        summary = 'Required hosted checks are reporting but not green, so unattended GitHub readiness is not established.'
    else:
        ready = True
        reason = 'ready'
        summary = (
            'Hosted required checks are both enforced by GitHub and currently green, so unattended GitHub readiness is established.'
            if repo_enforcement_truth is not None
            else 'Required hosted checks are reporting green, so unattended GitHub readiness is established for the currently evaluated signal set.'
        )

    return {
        'verification_authority_profile': profile,
        'repo_check_contract': dict(contract),
        'required_check_truth': dict(truth),
        'repo_required_check_enforcement': dict(enforcement),
        'repo_required_check_enforcement_converged': enforcement.get('repo_required_check_enforcement_converged'),
        'unattended_execution_ready': ready,
        'operational_convergence_ready': ready,
        'operational_convergence_reason': reason,
        'summary': summary,
        'hosted_authority_probe_status': probe_status,
        'required_check_state': state,
        'required_checks_discovered': discovered,
        'hosted_checks_reported': hosted_reported,
        'enforcement_probe_status': str(enforcement_truth.get('enforcement_probe_status') or ''),
        'enforcement_source': str(enforcement_truth.get('enforcement_source') or ''),
        'repo_default_branch': str(contract['repo_default_branch']),
    }


def evaluate_merge_eligibility(
    *,
    accepted: bool,
    autonomous_merge_enabled: bool,
    local_validation_passed: bool,
    verification_authority_profile: Any = 'local_plus_required_ci',
    repo_check_contract: Mapping[str, Any] | None = None,
    required_check_truth: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    authority = evaluate_verification_authority(
        verification_authority_profile=verification_authority_profile,
        local_validation_passed=local_validation_passed,
        required_check_truth=canonical_required_check_truth(
            required_check_truth,
            verification_authority_profile=verification_authority_profile,
            repo_check_contract=repo_check_contract,
        ),
    )
    convergence = evaluate_hosted_authority_convergence(
        verification_authority_profile=verification_authority_profile,
        repo_check_contract=repo_check_contract,
        required_check_truth=authority['required_check_truth'],
    )
    if not accepted:
        eligible = False
        reason = 'task_not_accepted'
    elif not autonomous_merge_enabled:
        eligible = False
        reason = 'autonomous_merge_disabled'
    elif not bool(authority['verification_authority_satisfied']):
        eligible = False
        reason = str(authority['blocking_reason']) or 'verification_authority_unsatisfied'
    elif not bool(convergence['hosted_authority_converged']):
        eligible = False
        reason = str(convergence['hosted_authority_convergence_reason'])
    else:
        eligible = True
        reason = 'eligible'
    return {
        'accepted': bool(accepted),
        'autonomous_merge_enabled': bool(autonomous_merge_enabled),
        'local_validation_passed': bool(local_validation_passed),
        'merge_eligible_now': eligible,
        'merge_eligibility_reason': reason,
        'next_task_may_proceed': bool(eligible),
        'verification_authority': dict(authority),
        'hosted_authority_convergence': dict(convergence),
    }


def evaluate_project_merge_eligibility(
    *,
    project_contract: Mapping[str, Any] | None = None,
    accepted: bool,
    autonomous_merge_enabled: bool,
    local_validation_passed: bool,
    required_check_truth: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    from agents.lib.project_registry import project_merge_eligibility_contract, project_validation_matrix

    matrix = project_validation_matrix(project_contract)
    merge_contract = project_merge_eligibility_contract(project_contract)
    repo_contract = project_repo_check_contract(project_contract)
    result = evaluate_merge_eligibility(
        accepted=accepted,
        autonomous_merge_enabled=autonomous_merge_enabled,
        local_validation_passed=local_validation_passed,
        verification_authority_profile=matrix['verification_authority_profile'],
        repo_check_contract=repo_contract,
        required_check_truth=required_check_truth,
    )
    return {
        **result,
        'project_id': str(matrix['project_id']),
        'validation_matrix': dict(matrix),
        'merge_contract': dict(merge_contract),
        'repo_check_contract': dict(repo_contract),
    }


def project_verification_authority_profile(project_contract: Mapping[str, Any] | None = None) -> VerificationAuthorityProfile:
    from agents.lib.project_registry import project_validation_matrix

    matrix = project_validation_matrix(project_contract)
    return coerce_verification_authority_profile(matrix.get('verification_authority_profile'), 'local_only')


def project_repo_check_contract(project_contract: Mapping[str, Any] | None = None) -> dict[str, object]:
    from agents.lib.project_registry import project_validation_matrix

    matrix = project_validation_matrix(project_contract)
    return canonical_repo_check_contract(
        required_checks=matrix.get('repo_required_checks'),
        repo_check_contract_source=matrix.get('repo_check_contract_source'),
        hosted_checks_source=matrix.get('hosted_checks_source'),
        repo_default_branch=matrix.get('repo_default_branch'),
        enforcement_probe_strategy=matrix.get('enforcement_probe_strategy'),
    )


def evaluate_project_verification_authority(
    *,
    project_contract: Mapping[str, Any] | None = None,
    local_validation_passed: bool,
    required_check_truth: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    from agents.lib.project_registry import project_validation_matrix

    matrix = project_validation_matrix(project_contract)
    profile = project_verification_authority_profile(project_contract)
    repo_contract = project_repo_check_contract(project_contract)
    result = evaluate_verification_authority(
        verification_authority_profile=profile,
        local_validation_passed=local_validation_passed,
        required_check_truth=(
            required_check_truth
            if required_check_truth is not None
            else canonical_required_check_truth(
                verification_authority_profile=profile,
                repo_check_contract=repo_contract,
            )
        ),
    )
    return {
        **result,
        'project_id': str(matrix['project_id']),
        'validation_matrix': dict(matrix),
        'repo_check_contract': dict(repo_contract),
    }


def workspace_metadata_for_project(
    project_contract: dict[str, object] | None = None,
    *,
    workspace_root: str = "",
    repo_root: str = "",
) -> dict[str, object]:
    contract = dict(project_contract or {})

    resolved_workspace_root = (
        workspace_root
        or str(contract.get("project_workspace_root", "") or "")
        or str(contract.get("workspace_root", "") or "")
        or "."
    )
    resolved_repo_root = (
        repo_root
        or str(contract.get("project_repo_root", "") or "")
        or str(contract.get("repo_root", "") or "")
        or resolved_workspace_root
    )

    return {
        "project_id": str(contract.get("project_id", "") or ""),
        "project_workspace_root": resolved_workspace_root,
        "project_repo_root": resolved_repo_root,
        "workspace_root": resolved_workspace_root,
        "repo_root": resolved_repo_root,
        "workspace_type": str(contract.get("workspace_type", "") or ""),
        "project_identity_ambiguous": bool(contract.get("project_identity_ambiguous", False)),
    }

