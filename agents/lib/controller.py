from __future__ import annotations

from typing import Any, Mapping

from agents.lib.multi_agent_contract import canonical_role_artifact_envelope, canonical_role_handoff_state


def _coerce_str_list(value: object) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw in value or []:  # type: ignore[arg-type]
        text = str(raw or "").strip()
        if text and text not in seen:
            items.append(text)
            seen.add(text)
    return items


def decide_single_task_controller_action(
    *,
    task_path: str,
    developer_artifact: Mapping[str, Any] | None = None,
    verifier_artifact: Mapping[str, Any] | None = None,
    repair_artifact: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    developer = dict(developer_artifact or {})
    verifier = dict(verifier_artifact or {})
    repair = dict(repair_artifact or {})

    verifier_verdict = str(verifier.get("verdict") or "not_run")
    repair_required = bool(repair.get("repair_required", False))
    repair_budget_exhausted = bool(repair.get("repair_budget_exhausted", False))
    repair_selected = bool(repair.get("repair_attempt_selected", False))
    escalation_required = bool(repair.get("escalation_required", False))
    retry_count_observed = int(developer.get("retry_count_observed", 0) or 0)

    focused_replay_commands = _coerce_str_list(
        verifier.get("focused_results") or repair.get("focused_replay_commands") or []
    )
    broad_replay_commands = _coerce_str_list(
        verifier.get("full_results") or repair.get("broad_replay_commands") or []
    )
    likely_failure_family = str(
        verifier.get("likely_failure_family") or repair.get("likely_failure_family") or ""
    ).strip()

    if verifier_verdict == "pass":
        action = "accept"
        post_task_decision = "continue"
        next_task_may_proceed = True
        next_role_decision = "controller"
        summary = (
            "Controller accepted the bounded one-task run after developer output passed focused and broad validation."
        )
        instructions = "Persist the controller decision and allow the next queued task only if the scheduler policy permits it."
    elif repair_required and repair_selected and not repair_budget_exhausted and not escalation_required:
        action = "repair"
        post_task_decision = "stop"
        next_task_may_proceed = False
        next_role_decision = "builder"
        summary = (
            "Controller selected a bounded targeted repair attempt from verifier evidence and kept advancement blocked."
        )
        instructions = "Do not advance the queue. Route the next bounded attempt back through the developer lane using the selected focused replay evidence."
    else:
        action = "stop"
        post_task_decision = "stop"
        next_task_may_proceed = False
        next_role_decision = "operator" if escalation_required or repair_budget_exhausted else "controller"
        if escalation_required or repair_budget_exhausted:
            summary = (
                "Controller stopped the one-task run because the bounded repair lane is exhausted or escalation is required."
            )
            instructions = (
                "Stop honestly and hand the task back to supervised recovery with the verifier evidence and selected repair context."
            )
        else:
            summary = "Controller stopped the one-task run because verifier evidence did not justify autonomous advancement."
            instructions = "Keep the task in the bounded one-task lane and require explicit controller review before any further widening."

    role_outcome = "accepted" if action == "accept" else "retry_selected" if action == "repair" else "stopped"
    handoff_state = canonical_role_handoff_state(
        active_role="controller",
        prior_role="verifier",
        role_attempt_count=max(1, retry_count_observed + 1),
        handoff_reason="controller_final_decision",
        handoff_summary=summary,
        handoff_instructions=instructions,
        role_output_summary=summary,
        verifier_verdict=verifier_verdict,
        controller_next_role_decision=next_role_decision,
        role_outcome=role_outcome,
    )
    raw_payload = {
        "task_path": str(task_path or ""),
        "action": action,
        "post_task_decision": post_task_decision,
        "next_task_may_proceed": next_task_may_proceed,
        "next_role_decision": next_role_decision,
        "summary": summary,
        "instructions": instructions,
        "verifier_verdict": verifier_verdict,
        "likely_failure_family": likely_failure_family,
        "focused_replay_commands": focused_replay_commands,
        "broad_replay_commands": broad_replay_commands,
        "repair_attempt_selected": repair_selected,
        "repair_budget_exhausted": repair_budget_exhausted,
        "escalation_required": escalation_required,
        "repair_strategy": str(repair.get("repair_strategy") or ""),
        "route_rationale": str(repair.get("route_rationale") or ""),
        "triggering_evidence": dict(repair.get("triggering_evidence") or {}),
        "final_authority_role": "controller",
        "handoff_reason": "controller_final_decision",
        "handoff_state": handoff_state,
        "role_outcome": role_outcome,
    }
    envelope = canonical_role_artifact_envelope(
        raw_payload,
        envelope_type="controller_output",
        artifact_role="controller",
        task_path=str(task_path or ""),
        attempt_count=max(1, retry_count_observed + 1),
        summary=summary,
        role_outcome=role_outcome,
        proposed_next_role=next_role_decision,
        handoff_reason="controller_final_decision",
        handoff_summary=summary,
        handoff_instructions=instructions,
        verifier_verdict=verifier_verdict,
        post_task_decision=post_task_decision,
        next_task_may_proceed=next_task_may_proceed,
        focused_result_count=len(focused_replay_commands),
        full_result_count=len(broad_replay_commands),
    )
    raw_payload["artifact_envelope"] = envelope
    return raw_payload


__all__ = ["decide_single_task_controller_action"]
