from __future__ import annotations

from typing import Any, Literal, Mapping, cast

AgentRole = Literal["controller", "builder", "verifier"]
ControllerNextRoleDecision = Literal["controller", "builder", "verifier", "stop", "manual_patch", "blocked"]
RoleOutcome = Literal[
    "not_run",
    "controller_routed",
    "builder_patch_proposed",
    "builder_noop",
    "verification_passed",
    "verification_failed",
    "verification_blocked",
]
VerifierVerdict = Literal["not_run", "pass", "fail", "blocked"]

AGENT_ROLES: tuple[AgentRole, ...] = ("controller", "builder", "verifier")
SPECIALIST_ROLES: tuple[AgentRole, ...] = ("builder", "verifier")
CONTROLLER_NEXT_ROLE_DECISIONS: tuple[ControllerNextRoleDecision, ...] = (
    "controller",
    "builder",
    "verifier",
    "stop",
    "manual_patch",
    "blocked",
)
ROLE_OUTCOMES: tuple[RoleOutcome, ...] = (
    "not_run",
    "controller_routed",
    "builder_patch_proposed",
    "builder_noop",
    "verification_passed",
    "verification_failed",
    "verification_blocked",
)
VERIFIER_VERDICTS: tuple[VerifierVerdict, ...] = ("not_run", "pass", "fail", "blocked")
ROLE_HANDOFF_FIELDS: tuple[str, ...] = (
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
ALLOWED_ROLE_HANDOFFS: dict[AgentRole, tuple[AgentRole, ...]] = {
    "controller": ("builder", "verifier"),
    "builder": ("controller", "verifier"),
    "verifier": ("controller", "builder"),
}


def coerce_agent_role(value: Any, default: AgentRole = "controller") -> AgentRole:
    text = str(value or "").strip()
    if text in AGENT_ROLES:
        return cast(AgentRole, text)
    return default


def coerce_verifier_verdict(value: Any, default: VerifierVerdict = "not_run") -> VerifierVerdict:
    text = str(value or "").strip()
    if text in VERIFIER_VERDICTS:
        return cast(VerifierVerdict, text)
    return default


def coerce_controller_next_role_decision(
    value: Any,
    default: ControllerNextRoleDecision = "builder",
) -> ControllerNextRoleDecision:
    text = str(value or "").strip()
    if text in CONTROLLER_NEXT_ROLE_DECISIONS:
        return cast(ControllerNextRoleDecision, text)
    return default


def coerce_role_outcome(value: Any, default: RoleOutcome = "not_run") -> RoleOutcome:
    text = str(value or "").strip()
    if text in ROLE_OUTCOMES:
        return cast(RoleOutcome, text)
    return default


def allowed_role_handoff(from_role: Any, to_role: Any) -> bool:
    source = coerce_agent_role(from_role)
    target = coerce_agent_role(to_role)
    return target in ALLOWED_ROLE_HANDOFFS[source]


def controller_decides_next_role(
    *,
    current_role: Any,
    proposed_next_role: Any,
    proposed_by_role: Any,
) -> ControllerNextRoleDecision:
    proposer = coerce_agent_role(proposed_by_role)
    if proposer != "controller":
        return "controller"
    decision = coerce_controller_next_role_decision(proposed_next_role)
    if decision in AGENT_ROLES and not allowed_role_handoff(current_role, decision):
        return "controller"
    return decision


def canonical_role_handoff_state(
    payload: Mapping[str, Any] | None = None,
    *,
    active_role: Any | None = None,
    prior_role: Any | None = None,
    role_attempt_count: Any | None = None,
    handoff_reason: Any | None = None,
    handoff_summary: Any | None = None,
    handoff_instructions: Any | None = None,
    role_output_summary: Any | None = None,
    verifier_verdict: Any | None = None,
    controller_next_role_decision: Any | None = None,
    role_outcome: Any | None = None,
) -> dict[str, object]:
    data = payload or {}
    active = coerce_agent_role(active_role if active_role is not None else data.get("active_role"))
    prior_raw = prior_role if prior_role is not None else data.get("prior_role")
    prior = "" if not str(prior_raw or "").strip() else coerce_agent_role(prior_raw)
    attempts_raw = role_attempt_count if role_attempt_count is not None else data.get("role_attempt_count")
    try:
        attempts = max(0, int(attempts_raw or 0))
    except (TypeError, ValueError):
        attempts = 0
    decision_default: ControllerNextRoleDecision = "builder" if active == "controller" else "controller"
    return {
        "active_role": active,
        "prior_role": prior,
        "role_attempt_count": attempts,
        "handoff_reason": str(handoff_reason if handoff_reason is not None else data.get("handoff_reason") or ""),
        "handoff_summary": str(handoff_summary if handoff_summary is not None else data.get("handoff_summary") or ""),
        "handoff_instructions": str(
            handoff_instructions if handoff_instructions is not None else data.get("handoff_instructions") or ""
        ),
        "role_output_summary": str(
            role_output_summary if role_output_summary is not None else data.get("role_output_summary") or ""
        ),
        "verifier_verdict": coerce_verifier_verdict(
            verifier_verdict if verifier_verdict is not None else data.get("verifier_verdict")
        ),
        "controller_next_role_decision": coerce_controller_next_role_decision(
            controller_next_role_decision if controller_next_role_decision is not None else data.get("controller_next_role_decision"),
            default=decision_default,
        ),
        "role_outcome": coerce_role_outcome(role_outcome if role_outcome is not None else data.get("role_outcome")),
    }


def resume_role_handoff_state(payload: Mapping[str, Any] | None = None) -> dict[str, object]:
    state = canonical_role_handoff_state(payload)
    decision = coerce_controller_next_role_decision(state.get("controller_next_role_decision"), default="builder")
    active = coerce_agent_role(state.get("active_role"), default="controller")
    if active == "controller" and decision in AGENT_ROLES:
        pending_role = decision
    else:
        pending_role = active
    return {
        **state,
        "pending_role": pending_role,
        "controller_must_choose_next_role": active == "controller",
    }


def multi_agent_contract_snapshot() -> dict[str, object]:
    return {
        "roles": list(AGENT_ROLES),
        "specialist_roles": list(SPECIALIST_ROLES),
        "controller_next_role_decisions": list(CONTROLLER_NEXT_ROLE_DECISIONS),
        "role_outcomes": list(ROLE_OUTCOMES),
        "verifier_verdicts": list(VERIFIER_VERDICTS),
        "handoff_fields": list(ROLE_HANDOFF_FIELDS),
        "allowed_handoffs": {role: list(targets) for role, targets in ALLOWED_ROLE_HANDOFFS.items()},
        "controller_authority_over_next_role": True,
        "sequential_role_execution_only": True,
        # Bounded proof-facing compatibility aliases frozen in Task 100.
        "execution_mode": "sequential",
        "controller_authority": "final_decision",
        "runtime_portability_scope": "python_only",
    }


CONSUMER_BRIDGE_REQUIRED_FIELDS: tuple[str, ...] = (
    "workspace_root",
    "consumer_name",
    "validation_commands",
    "acceptance_evidence_commands",
    "protected_paths",
)
CONSUMER_BRIDGE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "bootstrap_commands",
    "artifact_output_paths",
    "merge_policy_constraints",
    "optional_consumer_policies",
)


def consumer_bridge_requirements() -> dict[str, object]:
    return {
        "required_fields": list(CONSUMER_BRIDGE_REQUIRED_FIELDS),
        "optional_fields": list(CONSUMER_BRIDGE_OPTIONAL_FIELDS),
        "supported_consumers": ["tradingbot", "generic_python"],
        "consumer_bridge_is_stable": True,
        "full_standalone_extraction_completed": False,
    }


def orchestrator_package_boundary_snapshot() -> dict[str, object]:
    return {
        "product_name": "orchestrator",
        "operates_inside_monorepo": True,
        "full_standalone_extraction_completed": False,
        "supported_consumers": ["tradingbot", "generic_python"],
        "public_contract_modules": [
            "agents.lib.multi_agent_contract",
            "agents.lib.project_workspace_adapter",
            "agents.run_task",
        ],
        "consumer_bridge": consumer_bridge_requirements(),
        "role_contract": multi_agent_contract_snapshot(),
    }
