from __future__ import annotations

from typing import Mapping

CLAIM_DISCIPLINE_VERSION = 1

PROOF_COMPLETE_PATTERNS: tuple[str, ...] = (
    " are complete",
    "proof complete",
    "proof-complete",
    "synchronized proof checkpoint is now complete through",
    "deterministic proof-backed slice currently covers",
    "repo now has deterministic proof for",
    "tasks 090–",
    "tasks 090-",
)

CLAIM_SCOPE_PATH_HINTS: tuple[str, ...] = (
    "README.md",
    "docs/README.md",
    "TRADINGBOT_PROJECT_STATE.md",
    "ORCHESTRATOR_PRODUCT_SPEC.md",
    "ROADMAP",
    "roadmap",
    "status",
)

def claim_discipline_snapshot() -> dict[str, object]:
    return {
        "claim_discipline_version": CLAIM_DISCIPLINE_VERSION,
        "proof_complete_patterns": list(PROOF_COMPLETE_PATTERNS),
        "claim_scope_path_hints": list(CLAIM_SCOPE_PATH_HINTS),
        "requires_focused_green_for_proof_complete": True,
        "requires_full_green_for_proof_complete": True,
    }

def is_claim_scope_path(path: str) -> bool:
    text = str(path or "").strip()
    return any(hint in text for hint in CLAIM_SCOPE_PATH_HINTS)

def contains_proof_complete_claim(text: str) -> bool:
    lowered = str(text or "").lower()
    return any(pattern in lowered for pattern in PROOF_COMPLETE_PATTERNS)

def evaluate_claim_discipline(
    *,
    focused_validation_green: bool,
    full_validation_green: bool,
    proposed_updates: Mapping[str, str] | None = None,
) -> dict[str, object]:
    updates = dict(proposed_updates or {})
    proof_claim_gate_satisfied = bool(focused_validation_green) and bool(full_validation_green)

    claim_scope_paths: list[str] = []
    proof_claim_paths: list[str] = []
    blocked_claim_paths: list[str] = []
    truthful_recovery_paths: list[str] = []

    for path, text in updates.items():
        if not is_claim_scope_path(path):
            continue
        claim_scope_paths.append(path)
        if contains_proof_complete_claim(text):
            proof_claim_paths.append(path)
            if not proof_claim_gate_satisfied:
                blocked_claim_paths.append(path)
        else:
            truthful_recovery_paths.append(path)

    return {
        "focused_validation_green": bool(focused_validation_green),
        "full_validation_green": bool(full_validation_green),
        "proof_claim_gate_satisfied": proof_claim_gate_satisfied,
        "proof_claim_updates_allowed": proof_claim_gate_satisfied,
        "docs_overclaim_blocked": bool(blocked_claim_paths),
        "blocked_claim_paths": blocked_claim_paths,
        "allowed_claim_paths": [path for path in proof_claim_paths if path not in blocked_claim_paths],
        "proof_claim_paths": proof_claim_paths,
        "truthful_recovery_paths": truthful_recovery_paths,
        "claim_scope_paths": claim_scope_paths,
        "claim_gate_reason": (
            "focused_and_full_validation_green"
            if proof_claim_gate_satisfied
            else "proof_complete_wording_requires_focused_and_full_green"
        ),
    }

def filter_claim_updates_for_validation(
    *,
    focused_validation_green: bool,
    full_validation_green: bool,
    proposed_updates: Mapping[str, str] | None = None,
) -> dict[str, object]:
    updates = dict(proposed_updates or {})
    decision = evaluate_claim_discipline(
        focused_validation_green=focused_validation_green,
        full_validation_green=full_validation_green,
        proposed_updates=updates,
    )
    blocked = set(str(path) for path in decision["blocked_claim_paths"])
    allowed_updates = {path: text for path, text in updates.items() if path not in blocked}
    return {
        **decision,
        "allowed_updates": allowed_updates,
        "blocked_updates": {path: updates[path] for path in blocked if path in updates},
    }
