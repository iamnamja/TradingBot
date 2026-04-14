from __future__ import annotations

from typing import Any, Mapping, Sequence, cast


Role = str

# Canonical shared role vocabulary
AGENT_ROLES: tuple[Role, Role, Role] = ("controller", "builder", "verifier")
SPECIALIST_ROLES: tuple[Role, Role] = ("builder", "verifier")
CONTROLLER_NEXT_ROLE_DECISIONS: tuple[str, str, str, str, str, str] = (
    "controller",
    "builder",
    "verifier",
    "stop",
    "manual_patch",
    "blocked",
)
ROLE_OUTCOMES: tuple[str, ...] = (
    "not_run",
    "controller_routed",
    "builder_patch_proposed",
    "builder_noop",
    "verification_passed",
    "verification_failed",
    "verification_blocked",
)
VERIFIER_VERDICTS: tuple[str, ...] = ("not_run", "pass", "fail", "blocked")
ARTIFACT_ENVELOPE_TYPES: tuple[str, str, str] = ("coder_output", "tester_output", "controller_output")
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
    "role",
    "task_path",
    "attempt_count",
    "summary",
    "role_outcome",
    "proposed_next_role",
    "controller_next_role_decision",
    "handoff_reason",
    "handoff_summary",
    "handoff_instructions",
    "role_output_summary",
    "verifier_verdict",
    "acceptance_decision",
    "post_task_decision",
    "next_task_may_proceed",
    "verification_authority_profile",
    "changed_files",
    "focused_result_count",
    "full_result_count",
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
    "verification_authority_profile",
    "changed_files",
    "focused_result_count",
    "full_result_count",
)
ROLE_ARTIFACT_ENVELOPE_FIELD_NAMES: tuple[str, ...] = (
    "coder_artifact_envelope",
    "tester_artifact_envelope",
    "controller_artifact_envelope",
)

_PILOT_ROLE_ALIASES: dict[str, Role] = {
    "dev": "builder",
    "test": "verifier",
}
_ALLOWED_ROLE_HANDOFFS: dict[Role, tuple[Role, ...]] = {
    "controller": ("builder", "verifier"),
    "builder": ("controller", "verifier"),
    "verifier": ("controller", "builder"),
}
_ROLE_TO_ENVELOPE_TYPE: dict[Role, str] = {
    "builder": "coder_output",
    "verifier": "tester_output",
    "controller": "controller_output",
}


def _normalize_role(role: str | None) -> Role:
    token = str(role or "").strip().lower()
    if not token:
        return ""
    return cast(Role, _PILOT_ROLE_ALIASES.get(token, token))


def _normalize_changed_files(value: Any) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for raw in value or []:
        path = str(raw or "").strip().replace("\\", "/")
        if path and path not in seen:
            files.append(path)
            seen.add(path)
    return files


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _infer_envelope_type(role: str) -> str:
    normalized = _normalize_role(role)
    return _ROLE_TO_ENVELOPE_TYPE.get(normalized, "role_output")


def multi_agent_contract_snapshot() -> dict[str, object]:
    """Frozen/shared controller-contract snapshot. Extend only."""
    return {
        "schema_version": 1,
        "roles": list(AGENT_ROLES),
        "agent_roles": list(AGENT_ROLES),
        "specialist_roles": list(SPECIALIST_ROLES),
        "controller_next_role_decisions": list(CONTROLLER_NEXT_ROLE_DECISIONS),
        "allowed_controller_next_role_decisions": list(CONTROLLER_NEXT_ROLE_DECISIONS),
        "role_outcomes": list(ROLE_OUTCOMES),
        "verifier_verdicts": list(VERIFIER_VERDICTS),
        "artifact_envelope_types": list(ARTIFACT_ENVELOPE_TYPES),
        "handoff_fields": list(ROLE_HANDOFF_FIELDS),
        "role_handoff_fields": list(ROLE_HANDOFF_FIELDS),
        "artifact_envelope_fields": list(ARTIFACT_ENVELOPE_FIELDS),
        "artifact_envelope_summary_fields": list(ARTIFACT_ENVELOPE_SUMMARY_FIELDS),
        "role_artifact_envelope_field_names": list(ROLE_ARTIFACT_ENVELOPE_FIELD_NAMES),
        "allowed_role_handoffs": {role: list(targets) for role, targets in _ALLOWED_ROLE_HANDOFFS.items()},
        "allowed_handoffs": {role: list(targets) for role, targets in _ALLOWED_ROLE_HANDOFFS.items()},
        "pilot_role_aliases": dict(_PILOT_ROLE_ALIASES),
        "controller_authority_over_next_role": True,
        "sequential_role_execution_only": True,
    }


def allowed_role_handoff(current_role: str, next_role: str) -> bool:
    current = _normalize_role(current_role)
    nxt = _normalize_role(next_role)
    if current not in AGENT_ROLES or nxt not in AGENT_ROLES:
        return False
    return nxt in _ALLOWED_ROLE_HANDOFFS[current]


def controller_decides_next_role(
    *,
    current_role: str,
    proposed_next_role: str,
    proposed_by_role: str = "controller",
) -> str:
    # Only the controller may authoritatively choose the next role/decision.
    if _normalize_role(proposed_by_role) != "controller":
        return "controller"
    decision = _normalize_role(proposed_next_role) or str(proposed_next_role or "").strip()
    if decision in CONTROLLER_NEXT_ROLE_DECISIONS:
        if decision in AGENT_ROLES and not allowed_role_handoff("controller", decision):
            return "controller"
        return decision
    return "controller"


def canonical_role_handoff_state(
    *,
    active_role: str,
    prior_role: str | None = None,
    role_attempt_count: int | None = None,
    handoff_reason: str | None = None,
    handoff_summary: str | None = None,
    handoff_instructions: str | None = None,
    role_output_summary: str | None = None,
    verifier_verdict: str | None = None,
    controller_next_role_decision: str | None = None,
    role_outcome: str | None = None,
) -> dict[str, object]:
    active = _normalize_role(active_role)
    prior = _normalize_role(prior_role)
    decision = _normalize_role(controller_next_role_decision) or str(controller_next_role_decision or "controller")
    verdict = str(verifier_verdict or "not_run")
    if verdict not in VERIFIER_VERDICTS:
        verdict = "not_run"
    outcome = str(role_outcome or "not_run")
    if outcome not in ROLE_OUTCOMES:
        outcome = "not_run"

    state = {
        "active_role": active,
        "prior_role": prior,
        "role_attempt_count": max(0, _coerce_int(role_attempt_count, 0)),
        "handoff_reason": str(handoff_reason or ""),
        "handoff_summary": str(handoff_summary or ""),
        "handoff_instructions": str(handoff_instructions or ""),
        "role_output_summary": str(role_output_summary or handoff_summary or ""),
        "verifier_verdict": verdict,
        "controller_next_role_decision": decision,
        "role_outcome": outcome,
    }
    return resume_role_handoff_state(state)


def resume_role_handoff_state(
    handoff_state: Mapping[str, Any] | None,
    *,
    active_role: str | None = None,
    prior_role: str | None = None,
    role_attempt_count: int | None = None,
) -> dict[str, object]:
    payload = dict(handoff_state or {})
    active = _normalize_role(active_role if active_role is not None else payload.get("active_role"))
    prior = _normalize_role(prior_role if prior_role is not None else payload.get("prior_role"))
    attempts = max(0, _coerce_int(role_attempt_count if role_attempt_count is not None else payload.get("role_attempt_count"), 0))
    decision = _normalize_role(payload.get("controller_next_role_decision")) or str(payload.get("controller_next_role_decision") or "controller")
    if active == "controller" and decision in {"controller", "builder", "verifier"}:
        pending = decision
    else:
        pending = active or "controller"
    return {
        "active_role": active,
        "prior_role": prior,
        "role_attempt_count": attempts,
        "handoff_reason": str(payload.get("handoff_reason") or ""),
        "handoff_summary": str(payload.get("handoff_summary") or ""),
        "handoff_instructions": str(payload.get("handoff_instructions") or ""),
        "role_output_summary": str(payload.get("role_output_summary") or payload.get("handoff_summary") or ""),
        "verifier_verdict": str(payload.get("verifier_verdict") or "not_run"),
        "controller_next_role_decision": decision,
        "role_outcome": str(payload.get("role_outcome") or "not_run"),
        "pending_role": pending,
        "controller_must_choose_next_role": active == "controller",
    }


def canonical_role_artifact_envelope(
    raw_payload: Mapping[str, Any] | None = None,
    /,
    **kwargs: Any,
) -> dict[str, object]:
    payload = dict(raw_payload or {})
    artifact_role = _normalize_role(
        kwargs.get("artifact_role") or kwargs.get("role") or payload.get("artifact_role") or payload.get("role")
    )
    envelope_type = str(kwargs.get("envelope_type") or payload.get("envelope_type") or _infer_envelope_type(artifact_role))
    task_path = str(kwargs.get("task_path") or payload.get("task_path") or "")
    attempt_count = max(0, _coerce_int(kwargs.get("attempt_count") if "attempt_count" in kwargs else payload.get("attempt_count"), 0))
    summary = str(kwargs.get("summary") or payload.get("summary") or "")
    role_outcome = str(kwargs.get("role_outcome") or payload.get("role_outcome") or "not_run")
    proposed_next_role = _normalize_role(
        kwargs.get("proposed_next_role") or payload.get("proposed_next_role") or payload.get("controller_next_role_decision")
    )
    changed_files = _normalize_changed_files(kwargs.get("changed_files") if "changed_files" in kwargs else payload.get("changed_files"))
    focused_results = list(kwargs.get("focused_results") or payload.get("focused_results") or [])
    full_results = list(kwargs.get("full_results") or payload.get("full_results") or [])
    verifier_verdict = str(kwargs.get("verifier_verdict") or payload.get("verifier_verdict") or payload.get("verdict") or "not_run")
    acceptance_report = dict(payload.get("acceptance_report") or {})
    acceptance_decision = kwargs.get("acceptance_decision", payload.get("acceptance_decision", acceptance_report.get("acceptance_decision")))
    post_task_decision = kwargs.get("post_task_decision", payload.get("post_task_decision", acceptance_report.get("post_task_decision")))
    next_task_may_proceed = kwargs.get("next_task_may_proceed", payload.get("next_task_may_proceed", acceptance_report.get("next_task_may_proceed")))
    verification_authority_profile = str(kwargs.get("verification_authority_profile") or payload.get("verification_authority_profile") or "")
    handoff_reason = str(kwargs.get("handoff_reason") or payload.get("handoff_reason") or "")
    handoff_summary = str(kwargs.get("handoff_summary") or payload.get("handoff_summary") or summary)
    handoff_instructions = str(kwargs.get("handoff_instructions") or payload.get("handoff_instructions") or "")
    role_output_summary = str(kwargs.get("role_output_summary") or payload.get("role_output_summary") or summary)
    handoff_state = canonical_role_handoff_state(
        active_role=artifact_role,
        prior_role=str(payload.get("prior_role") or ""),
        role_attempt_count=kwargs.get("role_attempt_count") if "role_attempt_count" in kwargs else payload.get("role_attempt_count"),
        handoff_reason=handoff_reason,
        handoff_summary=handoff_summary,
        handoff_instructions=handoff_instructions,
        role_output_summary=role_output_summary,
        verifier_verdict=verifier_verdict,
        controller_next_role_decision=proposed_next_role or "controller",
        role_outcome=role_outcome,
    )
    return {
        "schema_version": 1,
        "envelope_type": envelope_type,
        "artifact_role": artifact_role,
        "role": artifact_role,
        "task_path": task_path,
        "attempt_count": attempt_count,
        "summary": summary,
        "role_outcome": role_outcome,
        "proposed_next_role": proposed_next_role,
        "controller_next_role_decision": proposed_next_role,
        "handoff_reason": handoff_reason,
        "handoff_summary": handoff_summary,
        "handoff_instructions": handoff_instructions,
        "role_output_summary": role_output_summary,
        "verifier_verdict": verifier_verdict,
        "acceptance_decision": acceptance_decision,
        "post_task_decision": post_task_decision,
        "next_task_may_proceed": next_task_may_proceed,
        "verification_authority_profile": verification_authority_profile,
        "changed_files": changed_files,
        "focused_result_count": len(focused_results),
        "full_result_count": len(full_results),
        "raw_payload": payload,
        "handoff_state": handoff_state,
    }


def summarize_role_artifact_envelope(
    envelope: Mapping[str, Any] | None,
    *,
    envelope_type: str | None = None,
    artifact_role: str | None = None,
) -> dict[str, object]:
    canonical = canonical_role_artifact_envelope(
        envelope or {},
        envelope_type=envelope_type,
        artifact_role=artifact_role,
    )
    handoff = dict(canonical.get("handoff_state") or {})
    return {
        "schema_version": int(canonical.get("schema_version") or 1),
        "envelope_type": str(canonical.get("envelope_type") or ""),
        "artifact_role": str(canonical.get("artifact_role") or ""),
        "task_path": str(canonical.get("task_path") or ""),
        "attempt_count": int(canonical.get("attempt_count") or 0),
        "summary": str(canonical.get("summary") or ""),
        "role_outcome": str(canonical.get("role_outcome") or ""),
        "proposed_next_role": str(canonical.get("proposed_next_role") or ""),
        "verifier_verdict": str(canonical.get("verifier_verdict") or "not_run"),
        "acceptance_decision": canonical.get("acceptance_decision"),
        "post_task_decision": canonical.get("post_task_decision"),
        "next_task_may_proceed": canonical.get("next_task_may_proceed"),
        "verification_authority_profile": str(canonical.get("verification_authority_profile") or ""),
        "changed_files": list(canonical.get("changed_files") or []),
        "focused_result_count": int(canonical.get("focused_result_count") or 0),
        "full_result_count": int(canonical.get("full_result_count") or 0),
        "pending_role": str(handoff.get("pending_role") or ""),
    }


def empty_role_artifact_envelopes() -> dict[str, dict[str, object]]:
    builder = canonical_role_artifact_envelope(
        {},
        envelope_type="coder_output",
        artifact_role="builder",
        task_path="",
        attempt_count=0,
        summary="",
        role_outcome="not_run",
    )
    verifier = canonical_role_artifact_envelope(
        {},
        envelope_type="tester_output",
        artifact_role="verifier",
        task_path="",
        attempt_count=0,
        summary="",
        role_outcome="not_run",
    )
    controller = canonical_role_artifact_envelope(
        {},
        envelope_type="controller_output",
        artifact_role="controller",
        task_path="",
        attempt_count=0,
        summary="",
        role_outcome="not_run",
    )
    return {
        "coder_artifact_envelope": builder,
        "tester_artifact_envelope": verifier,
        "controller_artifact_envelope": controller,
        # compatibility aliases
        "builder_artifact_envelope": builder,
        "verifier_artifact_envelope": verifier,
    }


def consumer_bridge_requirements() -> dict[str, object]:
    return {
        "consumer_bridge_is_stable": True,
        "supported_consumers": ["tradingbot", "generic_python"],
    }


def orchestrator_package_boundary_snapshot() -> dict[str, object]:
    return {
        "product_name": "orchestrator",
        "operates_inside_monorepo": True,
        "full_standalone_extraction_completed": False,
        "supported_consumers": ["tradingbot", "generic_python"],
        "consumer_bridge": consumer_bridge_requirements(),
    }


def canonical_adjacent_task_handoff(
    *,
    dependency_task_path: str,
    next_task_path: str,
    previous_task_handoff: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    payload = dict(previous_task_handoff or {})
    next_task_may_proceed = bool(payload.get("next_task_may_proceed", False))
    reason = str(payload.get("reason") or "")
    if next_task_may_proceed:
        handoff_status = "handoff_ready"
        if not reason:
            reason = "dependency_reported_next_task_may_proceed_true"
    else:
        handoff_status = "handoff_incomplete" if not payload else "handoff_incompatible"
        if not reason:
            reason = "dependency_report_missing_or_blocked"
    return {
        "schema_version": 1,
        "dependency_task_path": str(dependency_task_path or ""),
        "next_task_path": str(next_task_path or ""),
        "handoff_status": handoff_status,
        "next_task_may_proceed": next_task_may_proceed,
        "reason": reason,
        "implicated_paths": list(payload.get("implicated_paths") or []),
        "verification_authority_profile": str(payload.get("verification_authority_profile") or ""),
    }


def canonical_adjacent_task_handoff_state(
    *,
    dependency_task_path: str,
    next_task_path: str,
    handoff_status: str,
    next_task_may_proceed: bool,
    reason: str,
    implicated_paths: Sequence[str] | None = None,
    verification_authority_profile: str | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "dependency_task_path": str(dependency_task_path or ""),
        "next_task_path": str(next_task_path or ""),
        "handoff_status": str(handoff_status or ""),
        "next_task_may_proceed": bool(next_task_may_proceed),
        "reason": str(reason or ""),
        "implicated_paths": list(implicated_paths or []),
        "verification_authority_profile": str(verification_authority_profile or ""),
    }


def pilot_role_alias(role: str) -> str:
    return _normalize_role(role)


def coerce_supervised_pilot_sequence(requested_sequence: Sequence[str]) -> list[str]:
    return [_normalize_role(item) for item in requested_sequence]


def validate_supervised_pilot_sequence(requested_sequence: Sequence[str]) -> dict[str, object]:
    normalized = coerce_supervised_pilot_sequence(requested_sequence)
    ok = normalized in (
        ["builder", "verifier", "controller"],
        ["verifier", "builder", "controller"],
    )
    return {
        "ok": ok,
        "reason": "" if ok else "unsupported_sequence",
        "normalized_sequence": normalized,
        "controller_gate_required": True,
    }
