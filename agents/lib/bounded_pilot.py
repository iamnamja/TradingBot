from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence


PilotRole = str


# Canonical roles preserved by the orchestrator.
ROLE_BUILDER = "builder"
ROLE_VERIFIER = "verifier"
ROLE_CONTROLLER = "controller"

# Pilot aliases to existing role taxonomy.
_ALIAS_MAP = {
    "dev": ROLE_BUILDER,
    "test": ROLE_VERIFIER,
    # Allow canonical roles to pass through unchanged as well.
    ROLE_BUILDER: ROLE_BUILDER,
    ROLE_VERIFIER: ROLE_VERIFIER,
    ROLE_CONTROLLER: ROLE_CONTROLLER,
}


_SUPPORTED_SEQUENCES = (
    (ROLE_BUILDER, ROLE_VERIFIER, ROLE_CONTROLLER),
    (ROLE_VERIFIER, ROLE_BUILDER, ROLE_CONTROLLER),
)


@dataclass(frozen=True)
class BoundedPilotPlan:
    # Normalized bounded sequence using canonical roles.
    sequence: List[PilotRole]
    # Whether the controller approval gate is required for next-role transitions.
    controller_gate_required: bool
    # Whether the plan was stopped conservatively (e.g., unsupported sequence).
    stopped: bool
    # Optional human-readable reason when stopped is True.
    stop_reason: Optional[str] = None
    # Mode indicator for reporting/checkpoints.
    mode: str = "bounded_pilot"


def normalize_pilot_role(role: str) -> Optional[PilotRole]:
    """
    Map pilot role aliases to canonical orchestrator roles.

    dev  -> builder
    test -> verifier

    Returns:
        Canonical role string or None if unknown.
    """
    if not isinstance(role, str):
        return None
    key = role.strip().lower()
    return _ALIAS_MAP.get(key)


def normalize_bounded_sequence(seq: Iterable[str]) -> List[PilotRole]:
    """
    Normalize an input sequence that may include pilot aliases into canonical roles.

    Unknown roles are filtered out to keep the sequence conservative by default.
    """
    normalized: List[PilotRole] = []
    for r in seq:
        nr = normalize_pilot_role(r)
        if nr:
            normalized.append(nr)
    return normalized


def is_supported_bounded_sequence(seq: Sequence[str]) -> bool:
    """
    Supported conservative bounded sequences:
      - builder -> verifier -> controller
      - verifier -> builder -> controller
    """
    norm = tuple(normalize_bounded_sequence(seq))
    return norm in _SUPPORTED_SEQUENCES


def plan_bounded_sequence(start_role: str) -> BoundedPilotPlan:
    """
    Produce a conservative bounded pilot plan from a starting role.

    start_role in {dev|builder}   => [builder, verifier, controller]
    start_role in {test|verifier} => [verifier, builder, controller]

    Any other role will conservatively stop with an explicit reason.
    """
    nr = normalize_pilot_role(start_role)
    if nr == ROLE_BUILDER:
        seq = [ROLE_BUILDER, ROLE_VERIFIER, ROLE_CONTROLLER]
        return BoundedPilotPlan(sequence=seq, controller_gate_required=True, stopped=False)
    if nr == ROLE_VERIFIER:
        seq = [ROLE_VERIFIER, ROLE_BUILDER, ROLE_CONTROLLER]
        return BoundedPilotPlan(sequence=seq, controller_gate_required=True, stopped=False)
    if nr == ROLE_CONTROLLER:
        # Starting directly at controller is not supported for the pilot split.
        return BoundedPilotPlan(
            sequence=[ROLE_CONTROLLER],
            controller_gate_required=True,
            stopped=True,
            stop_reason="unsupported_sequence:start_at_controller",
        )
    return BoundedPilotPlan(
        sequence=[],
        controller_gate_required=True,
        stopped=True,
        stop_reason="unsupported_sequence:unknown_start_role",
    )


def enforce_bounded_sequence(seq: Iterable[str]) -> BoundedPilotPlan:
    """
    Normalize and enforce the bounded pilot conservative sequences.

    Produces a plan that either:
      - contains an allowed sequence and stopped=False
      - or stops conservatively with a reason
    """
    norm = normalize_bounded_sequence(seq)
    if is_supported_bounded_sequence(norm):
        return BoundedPilotPlan(sequence=list(norm), controller_gate_required=True, stopped=False)
    reason = "unsupported_sequence:" + "->".join(norm) if norm else "unsupported_sequence:empty_or_unknown"
    return BoundedPilotPlan(sequence=list(norm), controller_gate_required=True, stopped=True, stop_reason=reason)


def build_pilot_checkpoint(
    plan: BoundedPilotPlan,
    extra: Optional[dict] = None,
) -> dict:
    """
    Build an additive checkpoint/reporting payload to attach to existing single-task artifacts.

    Fields:
      - bounded_pilot: true
      - pilot_sequence: normalized canonical sequence
      - controller_gate_required: bool
      - stopped: bool
      - stop_reason: Optional[str]
      - mode: "bounded_pilot"
      - plus any extra fields provided
    """
    payload = {
        "bounded_pilot": True,
        "pilot_sequence": list(plan.sequence),
        "controller_gate_required": bool(plan.controller_gate_required),
        "stopped": bool(plan.stopped),
        "stop_reason": plan.stop_reason,
        "mode": plan.mode,
    }
    if extra:
        payload.update(extra)
    return payload


__all__ = [
    "ROLE_BUILDER",
    "ROLE_VERIFIER",
    "ROLE_CONTROLLER",
    "BoundedPilotPlan",
    "normalize_pilot_role",
    "normalize_bounded_sequence",
    "is_supported_bounded_sequence",
    "plan_bounded_sequence",
    "enforce_bounded_sequence",
    "build_pilot_checkpoint",
]
