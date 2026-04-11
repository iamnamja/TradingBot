from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


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


def decide_authority_gate(evidence: Dict[str, Any]) -> AuthorityGateDecision:
    category = classify_authority_evidence(evidence)

    if category is AuthorityEvidenceCategory.EXPLICIT_REQUIRED_CHECK_FAILURE:
        return AuthorityGateDecision(
            hard_block=True,
            category=category,
            reason="Explicit failure in a required check detected.",
            suggest_retry=False,
            retry_limit=0,
        )

    if category is AuthorityEvidenceCategory.POLICY_BLOCK:
        reason = "Policy indicates a blocking violation."
        policy = evidence.get("policy") or {}
        details = policy.get("reason") or policy.get("message")
        if isinstance(details, str) and details.strip():
            reason = f"{reason} {details}".strip()
        return AuthorityGateDecision(
            hard_block=True,
            category=category,
            reason=reason,
            suggest_retry=False,
            retry_limit=0,
        )

    if category is AuthorityEvidenceCategory.NO_CHECKS_REPORTED:
        return AuthorityGateDecision(
            hard_block=False,
            category=category,
            reason="No checks reported; allow bounded retry to reduce false authority blocks.",
            suggest_retry=True,
            retry_limit=1,
        )

    # Ambiguous or missing evidence: prefer a conservative bounded retry
    return AuthorityGateDecision(
        hard_block=False,
        category=category,
        reason="Ambiguous or incomplete authority evidence; prefer a bounded retry for corroboration.",
        suggest_retry=True,
        retry_limit=1,
    )


__all__ = [
    "AuthorityEvidenceCategory",
    "AuthorityGateDecision",
    "classify_authority_evidence",
    "decide_authority_gate",
]
