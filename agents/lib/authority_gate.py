from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Union


class AuthorityEvidenceCategory(str, Enum):
    NO_CHECKS_REPORTED = "no_checks_reported"
    EXPLICIT_REQUIRED_CHECK_FAILURE = "explicit_required_check_failure"
    POLICY_BLOCK = "policy_block"
    AMBIGUOUS_OR_MISSING_EVIDENCE = "ambiguous_or_missing_evidence"


@dataclass(frozen=True)
class AuthorityGateDecision:
    category: AuthorityEvidenceCategory
    hard_block: bool
    reason: str


EvidenceType = Union[str, Dict[str, Any], None]


def _detect_policy_block_from_dict(data: Dict[str, Any]) -> bool:
    if data.get("policy_block") is True:
        return True
    policy: Optional[Dict[str, Any]] = data.get("policy") if isinstance(data.get("policy"), dict) else None
    if policy:
        if policy.get("block") is True or policy.get("blocked") is True:
            return True
        msg = str(policy.get("message", "")).lower()
        if "policy block" in msg or "blocked by policy" in msg:
            return True
    return False


def _extract_checks_from_dict(data: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    # Normalized field names first
    checks = []
    for key in ("required_checks", "checks", "ci_checks", "statuses"):
        value = data.get(key)
        if isinstance(value, list):
            checks.extend([c for c in value if isinstance(c, dict)])
    # Sometimes nested under "ci" or "github"
    ci = data.get("ci")
    if isinstance(ci, dict):
        for key in ("required_checks", "checks", "statuses"):
            value = ci.get(key)
            if isinstance(value, list):
                checks.extend([c for c in value if isinstance(c, dict)])
    gh = data.get("github")
    if isinstance(gh, dict):
        for key in ("required_checks", "checks", "commit_statuses"):
            value = gh.get(key)
            if isinstance(value, list):
                checks.extend([c for c in value if isinstance(c, dict)])
    return checks


def _has_explicit_required_check_failure(data: Dict[str, Any]) -> bool:
    # Direct flags
    if data.get("required_checks_failed") is True:
        return True
    # Explore checks list for explicit "failed" states
    for check in _extract_checks_from_dict(data):
        status = str(check.get("status", "") or check.get("conclusion", "")).lower()
        required = check.get("required")
        # Treat as required if explicit or if typical required names; remain conservative for explicit failures
        is_required = bool(required) or str(check.get("name", "")).lower() in {
            "required", "ci", "tests", "lint", "build", "mergeable"
        }
        if status in {"failed", "failure", "error", "timed_out", "cancelled"} and is_required:
            return True
    return False


def classify_authority_evidence(evidence: EvidenceType) -> AuthorityGateDecision:
    # String evidence quick scan
    if isinstance(evidence, str):
        text = evidence.strip().lower()
        if not text:
            return AuthorityGateDecision(
                category=AuthorityEvidenceCategory.NO_CHECKS_REPORTED,
                hard_block=False,
                reason="Empty string evidence",
            )
        if "policy block" in text or "blocked by policy" in text:
            return AuthorityGateDecision(
                category=AuthorityEvidenceCategory.POLICY_BLOCK,
                hard_block=True,
                reason="String mentions a policy block",
            )
        if "required check" in text and ("fail" in text or "failed" in text or "failing" in text):
            return AuthorityGateDecision(
                category=AuthorityEvidenceCategory.EXPLICIT_REQUIRED_CHECK_FAILURE,
                hard_block=True,
                reason="String mentions explicit required check failure",
            )
        # Any other string is ambiguous
        return AuthorityGateDecision(
            category=AuthorityEvidenceCategory.AMBIGUOUS_OR_MISSING_EVIDENCE,
            hard_block=False,
            reason="String evidence is not explicit about a required check failure or policy block",
        )

    # Missing evidence
    if evidence is None:
        return AuthorityGateDecision(
            category=AuthorityEvidenceCategory.NO_CHECKS_REPORTED,
            hard_block=False,
            reason="No evidence provided",
        )

    # Dict evidence
    if isinstance(evidence, dict):
        if not evidence:
            return AuthorityGateDecision(
                category=AuthorityEvidenceCategory.NO_CHECKS_REPORTED,
                hard_block=False,
                reason="Empty evidence dictionary",
            )
        if _detect_policy_block_from_dict(evidence):
            return AuthorityGateDecision(
                category=AuthorityEvidenceCategory.POLICY_BLOCK,
                hard_block=True,
                reason="Policy block indicated by evidence",
            )
        if _has_explicit_required_check_failure(evidence):
            return AuthorityGateDecision(
                category=AuthorityEvidenceCategory.EXPLICIT_REQUIRED_CHECK_FAILURE,
                hard_block=True,
                reason="Explicit required check failure detected",
            )
        # If checks are mentioned but without explicit failure, it's ambiguous
        checks = list(_extract_checks_from_dict(evidence))
        if checks:
            return AuthorityGateDecision(
                category=AuthorityEvidenceCategory.AMBIGUOUS_OR_MISSING_EVIDENCE,
                hard_block=False,
                reason="Checks present without explicit required failure",
            )
        return AuthorityGateDecision(
            category=AuthorityEvidenceCategory.AMBIGUOUS_OR_MISSING_EVIDENCE,
            hard_block=False,
            reason="Evidence provided but not specific to required checks or policy block",
        )

    # Any other type is treated as ambiguous
    return AuthorityGateDecision(
        category=AuthorityEvidenceCategory.AMBIGUOUS_OR_MISSING_EVIDENCE,
        hard_block=False,
        reason=f"Unsupported evidence type: {type(evidence).__name__}",
    )


def should_hard_block(evidence: EvidenceType) -> bool:
    decision = classify_authority_evidence(evidence)
    return decision.hard_block
