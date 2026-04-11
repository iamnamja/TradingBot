from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Mapping


class AuthorityEvidenceCategory(str, Enum):
    NO_CHECKS_REPORTED = "no_checks_reported"
    EXPLICIT_REQUIRED_CHECK_FAILURE = "explicit_required_check_failure"
    POLICY_BLOCK = "policy_block"
    AMBIGUOUS_OR_MISSING_EVIDENCE = "ambiguous_or_missing_evidence"


@dataclass(frozen=True)
class AuthorityGateDecision:
    hard_block: bool
    category: AuthorityEvidenceCategory
    reason: str
    suggest_retry: bool = False
    retry_limit: int = 0


def _has_explicit_required_check_failure(evidence: Dict[str, Any]) -> bool:
    # Primary path: "required_checks" is a normalized structured list of check runs
    for item in evidence.get("required_checks", []) or []:
        status = str(item.get("status", "")).lower()
        required = bool(item.get("required", True))
        if required and status in {"failed", "failure", "error"}:
            return True

    # Fallback: generic "checks" with "required" annotation
    for item in evidence.get("checks", []) or []:
        status = str(item.get("status", "") or item.get("state", "")).lower()
        required = bool(item.get("required", False))
        if required and status in {"failed", "failure", "error"}:
            return True

    # Another possible shape: a summary object with explicit required failure flag
    if bool(evidence.get("required_checks_failed", False)):
        return True

    return False


def _has_policy_block(evidence: Dict[str, Any]) -> bool:
    policy = evidence.get("policy") or {}
    # Conservative: explicit "block" takes precedence
    if bool(policy.get("block", False)):
        return True
    # Or a machine-readable policy_block flag
    if bool(policy.get("policy_block", False)):
        return True
    # Or a violation list that is explicitly marked blocking
    violations = policy.get("violations") or policy.get("violation") or []
    if isinstance(violations, list):
        for v in violations:
            if isinstance(v, dict) and bool(v.get("blocking", False)):
                return True
    return False


def classify_authority_evidence(evidence: Dict[str, Any]) -> AuthorityEvidenceCategory:
    if not evidence or (
        not evidence.get("required_checks")
        and not evidence.get("checks")
        and not evidence.get("policy")
        and not evidence.get("required_checks_failed")
    ):
        return AuthorityEvidenceCategory.NO_CHECKS_REPORTED

    if _has_policy_block(evidence):
        return AuthorityEvidenceCategory.POLICY_BLOCK

    if _has_explicit_required_check_failure(evidence):
        return AuthorityEvidenceCategory.EXPLICIT_REQUIRED_CHECK_FAILURE

    return AuthorityEvidenceCategory.AMBIGUOUS_OR_MISSING_EVIDENCE


def _message_indicates_timing_artifact(message: str) -> bool:
    lower = str(message or "").strip().lower()
    if not lower:
        return False
    return any(
        token in lower
        for token in (
            "not yet reported",
            "no checks reported",
            "no required checks reported",
            "settle window",
            "cli timing",
        )
    )


def determine_corroboration_state(
    *,
    evidence: Mapping[str, Any] | None = None,
    message: str = "",
    ok: bool = False,
    step: str = "",
) -> str:
    """
    Lightweight corroboration classifier for benchmark/session artifacts.

    Returns one of:
    - likely_cli_timing_artifact
    - unresolved_authority_ambiguity
    - confirmed_authority_block
    """
    ev = dict(evidence or {})
    # Confirmed blocks first
    if _has_policy_block(ev) or _has_explicit_required_check_failure(ev):
        return "confirmed_authority_block"

    # Timing artifact heuristics (e.g., GH CLI settle window)
    hosted_status = str(ev.get("hosted_authority_probe_status", "") or "").strip().lower()
    if hosted_status == "not_yet_reported" or _message_indicates_timing_artifact(message):
        return "likely_cli_timing_artifact"

    # Default conservative ambiguity umbrella
    return "unresolved_authority_ambiguity"


def decide_authority_gate(
    evidence: Dict[str, Any] | None = None,
    *,
    classification: Mapping[str, Any] | None = None,
    category: str = "",
    message: str = "",
    ok: bool = False,
    step: str = "",
) -> AuthorityGateDecision | Dict[str, object]:
    """
    Backward-compatible authority gate decision.

    - Legacy mode: decide_authority_gate(evidence) -> AuthorityGateDecision dataclass
    - Enriched mode (opt-in): decide_authority_gate(classification=..., message=..., evidence=..., ok=..., step=...)
      -> dict with corroboration_state persisted for benchmark artifacts.
    """
    # Normalize evidence
    ev = dict(evidence or {})
    # Resolve category from provided classification/category overrides
    if classification and isinstance(classification, Mapping):
        detected = str(classification.get("category") or "").strip()
    else:
        detected = str(category or "").strip()
    if not detected:
        detected = classify_authority_evidence(ev).value
    try:
        enum_category = AuthorityEvidenceCategory(detected)
    except Exception:
        # Fallback to conservative umbrella if unknown
        enum_category = AuthorityEvidenceCategory.AMBIGUOUS_OR_MISSING_EVIDENCE

    # Enriched mode if any corroboration-related context is provided
    enriched_mode = bool(classification or message or step or ok is not False or evidence is not None and "hosted_authority_probe_status" in ev)

    if not enriched_mode and (evidence is not None):
        # Legacy dataclass behavior
        if enum_category is AuthorityEvidenceCategory.EXPLICIT_REQUIRED_CHECK_FAILURE:
            return AuthorityGateDecision(
                hard_block=True,
                category=enum_category,
                reason="Explicit failure in a required check detected.",
                suggest_retry=False,
                retry_limit=0,
            )
        if enum_category is AuthorityEvidenceCategory.POLICY_BLOCK:
            reason = "Policy indicates a blocking violation."
            policy = ev.get("policy") or {}
            details = policy.get("reason") or policy.get("message")
            if isinstance(details, str) and details.strip():
                reason = f"{reason} {details}".strip()
            return AuthorityGateDecision(
                hard_block=True,
                category=enum_category,
                reason=reason,
                suggest_retry=False,
                retry_limit=0,
            )
        if enum_category is AuthorityEvidenceCategory.NO_CHECKS_REPORTED:
            return AuthorityGateDecision(
                hard_block=False,
                category=enum_category,
                reason="No checks reported; allow bounded retry to reduce false authority blocks.",
                suggest_retry=True,
                retry_limit=1,
            )
        return AuthorityGateDecision(
            hard_block=False,
            category=enum_category,
            reason="Ambiguous or incomplete authority evidence; prefer a bounded retry for corroboration.",
            suggest_retry=True,
            retry_limit=1,
        )

    # Enriched mapping behavior for benchmark/re-proof persistence
    corroboration_state = determine_corroboration_state(evidence=ev, message=message, ok=ok, step=step)

    if enum_category in {AuthorityEvidenceCategory.POLICY_BLOCK, AuthorityEvidenceCategory.EXPLICIT_REQUIRED_CHECK_FAILURE}:
        decision_text = "hard_block"
        note = "Policy indicates a blocking violation." if enum_category is AuthorityEvidenceCategory.POLICY_BLOCK else "Explicit failure in a required check detected."
        policy = ev.get("policy") or {}
        details = policy.get("reason") or policy.get("message")
        if isinstance(details, str) and details.strip() and enum_category is AuthorityEvidenceCategory.POLICY_BLOCK:
            note = f"{note} {details}".strip()
        return {
            "decision": decision_text,
            "category": enum_category.value,
            "corroboration_state": corroboration_state,
            "ok": False,
            "note": note,
            "retry_limit": 0,
            "suggest_retry": False,
            "step": str(step or ""),
            "message": str(message or ""),
            "evidence": ev,
        }

    # Conservative bounded retry for all non-confirmed states (timing artifact and ambiguity alike)
    decision_text = "bounded_retry"
    note = (
        "No checks reported; allow bounded retry to reduce false authority blocks."
        if enum_category is AuthorityEvidenceCategory.NO_CHECKS_REPORTED
        else "Ambiguous or incomplete authority evidence; prefer a bounded retry for corroboration."
    )
    return {
        "decision": decision_text,
        "category": enum_category.value,
        "corroboration_state": corroboration_state,
        "ok": False,
        "note": note,
        "retry_limit": 1,
        "suggest_retry": True,
        "step": str(step or ""),
        "message": str(message or ""),
        "evidence": ev,
    }


__all__ = [
    "AuthorityEvidenceCategory",
    "AuthorityGateDecision",
    "classify_authority_evidence",
    "determine_corroboration_state",
    "decide_authority_gate",
]
