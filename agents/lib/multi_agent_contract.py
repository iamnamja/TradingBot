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
ArtifactEnvelopeType = Literal["coder_output", "tester_output", "controller_output"]

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
ARTIFACT_ENVELOPE_TYPES: tuple[ArtifactEnvelopeType, ...] = ("coder_output", "tester_output", "controller_output")
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
ARTIFACT_ENVELOPE_FIELDS: tuple[str, ...] = (
    "schema_version",
    "envelope_type",
    "artifact_role",
    "task_path",
    "attempt_count",
    "summary",
    "role_outcome",
    "proposed_next_role",
    "handoff_reason",
    "handoff_summary",
    "handoff_instructions",
    "verifier_verdict",
    "acceptance_decision",
    "post_task_decision",
    "next_task_may_proceed",
    "changed_files",
    "focused_result_count",
    "full_result_count",
    "verification_authority_profile",
    "raw_payload",
)
ARTIFACT_ENVELOPE_SUMMARY_FIELDS: tuple[str, ...] = (
    "schema_version",
    "envelope_type",
    "artifact_role",
    "task_path",
    "attempt_count",
    "summary",
    "role_outcome",
    "proposed_next_role",
    "verifier_verdict",
    "acceptance_decision",
    "post_task_decision",
    "next_task_may_proceed",
    "changed_files",
    "focused_result_count",
    "full_result_count",
    "verification_authority_profile",
)
ROLE_ARTIFACT_ENVELOPE_FIELD_NAMES: tuple[str, ...] = (
    "coder_artifact_envelope",
    "tester_artifact_envelope",
    "controller_artifact_envelope",
)
ALLOWED_ROLE_HANDOFFS: dict[AgentRole, tuple[AgentRole, ...]] = {
    "controller": ("builder", "verifier"),
    "builder": ("controller", "verifier"),
    "verifier": ("controller", "builder"),
}
_ROLE_TO_ARTIFACT_TYPE: dict[AgentRole, ArtifactEnvelopeType] = {
    "builder": "coder_output",
    "verifier": "tester_output",
    "controller": "controller_output",
}


def _coerce_string(value: Any) -> str:
    return str(value or "")


def _coerce_int(value: Any, default: int = 0, *, minimum: int = 0) -> int:
    try:
        return max(minimum, int(value or default))
    except (TypeError, ValueError):
        return default


def _coerce_changed_files(value: Any) -> list[str]:
    changed: list[str] = []
    seen: set[str] = set()
    for raw in value or []:
        path = str(raw or "").strip().replace("\\", "/")
        if path and path not in seen:
            changed.append(path)
            seen.add(path)
    return changed


def _json_safe_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_copy(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


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


def coerce_artifact_envelope_type(
    value: Any,
    default: ArtifactEnvelopeType = "controller_output",
) -> ArtifactEnvelopeType:
    text = str(value or "").strip()
    if text in ARTIFACT_ENVELOPE_TYPES:
        return cast(ArtifactEnvelopeType, text)
    return default


def artifact_envelope_type_for_role(role: Any) -> ArtifactEnvelopeType:
    return _ROLE_TO_ARTIFACT_TYPE[coerce_agent_role(role)]


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
    attempts = _coerce_int(attempts_raw, minimum=0)
    decision_default: ControllerNextRoleDecision = "builder" if active == "controller" else "controller"
    return {
        "active_role": active,
        "prior_role": prior,
        "role_attempt_count": attempts,
        "handoff_reason": _coerce_string(handoff_reason if handoff_reason is not None else data.get("handoff_reason")),
        "handoff_summary": _coerce_string(handoff_summary if handoff_summary is not None else data.get("handoff_summary")),
        "handoff_instructions": _coerce_string(
            handoff_instructions if handoff_instructions is not None else data.get("handoff_instructions")
        ),
        "role_output_summary": _coerce_string(
            role_output_summary if role_output_summary is not None else data.get("role_output_summary")
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


def canonical_role_artifact_envelope(
    payload: Mapping[str, Any] | None = None,
    *,
    envelope_type: Any | None = None,
    artifact_role: Any | None = None,
    task_path: Any | None = None,
    attempt_count: Any | None = None,
    summary: Any | None = None,
    role_outcome: Any | None = None,
    proposed_next_role: Any | None = None,
    handoff_reason: Any | None = None,
    handoff_summary: Any | None = None,
    handoff_instructions: Any | None = None,
    verifier_verdict: Any | None = None,
    acceptance_decision: Any | None = None,
    post_task_decision: Any | None = None,
    next_task_may_proceed: Any | None = None,
    changed_files: Any | None = None,
    focused_result_count: Any | None = None,
    full_result_count: Any | None = None,
    verification_authority_profile: Any | None = None,
    raw_payload: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    data = dict(payload or {})
    acceptance_report = dict(data.get("acceptance_report") or {})
    role_default = "controller"
    if str(data.get("role") or "").strip() in AGENT_ROLES:
        role_default = str(data.get("role"))
    role = coerce_agent_role(
        artifact_role if artifact_role is not None else data.get("artifact_role") or data.get("role"),
        default=cast(AgentRole, role_default),
    )
    inferred_type = artifact_envelope_type_for_role(role)
    artifact_type = coerce_artifact_envelope_type(
        envelope_type if envelope_type is not None else data.get("envelope_type"),
        default=inferred_type,
    )
    summary_value = _coerce_string(
        summary
        if summary is not None
        else data.get("summary")
        or data.get("output_summary")
        or data.get("validator_note")
        or acceptance_report.get("note")
    )
    raw = raw_payload if raw_payload is not None else (data.get("raw_payload") if isinstance(data.get("raw_payload"), Mapping) else data)
    return {
        "schema_version": 1,
        "envelope_type": artifact_type,
        "artifact_role": role,
        "task_path": _coerce_string(task_path if task_path is not None else data.get("task_path")),
        "attempt_count": _coerce_int(
            attempt_count if attempt_count is not None else data.get("attempt_count") or data.get("role_attempt_count"),
            minimum=0,
        ),
        "summary": summary_value,
        "role_outcome": _coerce_string(role_outcome if role_outcome is not None else data.get("role_outcome")),
        "proposed_next_role": _coerce_string(
            proposed_next_role
            if proposed_next_role is not None
            else data.get("proposed_next_role")
            or data.get("next_role_decision")
            or data.get("controller_next_role_decision")
        ),
        "handoff_reason": _coerce_string(handoff_reason if handoff_reason is not None else data.get("handoff_reason")),
        "handoff_summary": _coerce_string(handoff_summary if handoff_summary is not None else data.get("handoff_summary")),
        "handoff_instructions": _coerce_string(
            handoff_instructions if handoff_instructions is not None else data.get("handoff_instructions") or data.get("instructions")
        ),
        "verifier_verdict": _coerce_string(
            verifier_verdict if verifier_verdict is not None else data.get("verifier_verdict") or data.get("verdict")
        ),
        "acceptance_decision": _coerce_string(
            acceptance_decision
            if acceptance_decision is not None
            else data.get("acceptance_decision")
            or acceptance_report.get("acceptance_decision")
        ),
        "post_task_decision": _coerce_string(
            post_task_decision
            if post_task_decision is not None
            else data.get("post_task_decision")
            or acceptance_report.get("post_task_decision")
        ),
        "next_task_may_proceed": bool(
            next_task_may_proceed
            if next_task_may_proceed is not None
            else data.get("next_task_may_proceed")
            if data.get("next_task_may_proceed") is not None
            else acceptance_report.get("next_task_may_proceed", False)
        ),
        "changed_files": _coerce_changed_files(changed_files if changed_files is not None else data.get("changed_files")),
        "focused_result_count": _coerce_int(
            focused_result_count
            if focused_result_count is not None
            else data.get("focused_result_count")
            if data.get("focused_result_count") is not None
            else len(list(data.get("focused_results", []) or [])),
            minimum=0,
        ),
        "full_result_count": _coerce_int(
            full_result_count
            if full_result_count is not None
            else data.get("full_result_count")
            if data.get("full_result_count") is not None
            else len(list(data.get("full_results", []) or [])),
            minimum=0,
        ),
        "verification_authority_profile": _coerce_string(
            verification_authority_profile
            if verification_authority_profile is not None
            else data.get("verification_authority_profile")
        ),
        "raw_payload": cast(dict[str, object], _json_safe_copy(raw)),
    }


def summarize_role_artifact_envelope(payload: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, object]:
    envelope = canonical_role_artifact_envelope(payload, **overrides)
    return {field_name: envelope[field_name] for field_name in ARTIFACT_ENVELOPE_SUMMARY_FIELDS}


def empty_role_artifact_envelopes() -> dict[str, dict[str, object]]:
    return {
        "coder_artifact_envelope": canonical_role_artifact_envelope(envelope_type="coder_output", artifact_role="builder", raw_payload={}),
        "tester_artifact_envelope": canonical_role_artifact_envelope(envelope_type="tester_output", artifact_role="verifier", raw_payload={}),
        "controller_artifact_envelope": canonical_role_artifact_envelope(envelope_type="controller_output", artifact_role="controller", raw_payload={}),
    }


def multi_agent_contract_snapshot() -> dict[str, object]:
    return {
        "roles": list(AGENT_ROLES),
        "specialist_roles": list(SPECIALIST_ROLES),
        "controller_next_role_decisions": list(CONTROLLER_NEXT_ROLE_DECISIONS),
        "role_outcomes": list(ROLE_OUTCOMES),
        "verifier_verdicts": list(VERIFIER_VERDICTS),
        "handoff_fields": list(ROLE_HANDOFF_FIELDS),
        "artifact_envelope_types": list(ARTIFACT_ENVELOPE_TYPES),
        "artifact_envelope_fields": list(ARTIFACT_ENVELOPE_FIELDS),
        "artifact_envelope_summary_fields": list(ARTIFACT_ENVELOPE_SUMMARY_FIELDS),
        "role_artifact_envelope_field_names": list(ROLE_ARTIFACT_ENVELOPE_FIELD_NAMES),
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
