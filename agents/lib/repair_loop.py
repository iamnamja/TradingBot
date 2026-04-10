from __future__ import annotations

from typing import Any, Mapping

from agents.lib.multi_agent_contract import canonical_role_artifact_envelope


def _coerce_str_list(value: object) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw in value or []:  # type: ignore[arg-type]
        text = str(raw or "").strip()
        if text and text not in seen:
            items.append(text)
            seen.add(text)
    return items


def select_single_task_targeted_repair(
    *,
    task_path: str,
    developer_artifact: Mapping[str, Any] | None = None,
    verifier_artifact: Mapping[str, Any] | None = None,
    max_repair_attempts_within_run: int = 1,
) -> dict[str, object]:
    developer = dict(developer_artifact or {})
    verifier = dict(verifier_artifact or {})
    critique = dict(verifier.get("tester_critique_bundle") or {})
    verifier_verdict = str(verifier.get("verdict") or "not_run")
    retry_count_observed = int(developer.get("retry_count_observed", 0) or 0)
    focused_replay_commands = _coerce_str_list(
        critique.get("focused_replay_commands") or verifier.get("focused_results") or []
    )
    broad_replay_commands = _coerce_str_list(
        critique.get("broad_replay_commands") or verifier.get("full_results") or []
    )
    likely_failure_family = str(
        critique.get("likely_failure_family") or verifier.get("likely_failure_family") or ""
    ).strip()

    repair_required = verifier_verdict == "fail"
    repair_budget_remaining = max(0, int(max_repair_attempts_within_run or 0) - retry_count_observed)
    repair_budget_exhausted = repair_required and repair_budget_remaining <= 0

    if not repair_required:
        repair_strategy = "no_repair_required"
        remediation_lane = "controller"
        next_role = "controller"
        repair_attempt_selected = False
        escalation_required = verifier_verdict == "blocked"
        route_rationale = "Verifier evidence is already green or blocked outside the repair lane."
    elif focused_replay_commands and not repair_budget_exhausted:
        repair_strategy = "focused_replay_then_targeted_patch"
        remediation_lane = "developer_repair"
        next_role = "builder"
        repair_attempt_selected = True
        escalation_required = False
        route_rationale = "Verifier produced focused failing evidence, so the narrowest next repair stays in the developer lane."
    elif broad_replay_commands and not repair_budget_exhausted:
        repair_strategy = "broad_replay_then_targeted_patch"
        remediation_lane = "developer_repair"
        next_role = "builder"
        repair_attempt_selected = True
        escalation_required = False
        route_rationale = "Verifier lacked a narrow replay target, so the next bounded repair falls back to broad replay."
    else:
        repair_strategy = "supervised_escalation"
        remediation_lane = "supervised_recovery"
        next_role = "operator"
        repair_attempt_selected = False
        escalation_required = True
        route_rationale = "The bounded repair budget is exhausted or no credible replay target exists, so the task must escalate."

    summary = (
        "Repair selector kept the run green and returned control to the controller."
        if not repair_required
        else "Repair selector chose a bounded targeted replay from verifier evidence."
        if repair_attempt_selected
        else "Repair selector exhausted the bounded lane and escalated the task for supervised recovery."
    )
    triggering_evidence = {
        "likely_failure_family": likely_failure_family,
        "focused_replay_commands": focused_replay_commands,
        "broad_replay_commands": broad_replay_commands,
        "failure_clusters": list(critique.get("failure_clusters") or []),
        "retry_count_observed": retry_count_observed,
        "max_repair_attempts_within_run": int(max_repair_attempts_within_run or 0),
    }
    raw_payload = {
        "role": "repair",
        "artifact_kind": "single_task_repair_artifact",
        "task_path": str(task_path or ""),
        "repair_required": repair_required,
        "repair_attempt_selected": repair_attempt_selected,
        "repair_budget_remaining": repair_budget_remaining,
        "repair_budget_exhausted": repair_budget_exhausted,
        "repair_strategy": repair_strategy,
        "remediation_lane": remediation_lane,
        "next_role": next_role,
        "escalation_required": escalation_required,
        "route_rationale": route_rationale,
        "summary": summary,
        "focused_replay_commands": focused_replay_commands,
        "broad_replay_commands": broad_replay_commands,
        "likely_failure_family": likely_failure_family,
        "triggering_evidence": triggering_evidence,
        "role_outcome": "retry_selected" if repair_attempt_selected else "stopped" if escalation_required else "not_run",
        "proposed_next_role": next_role,
    }
    envelope = canonical_role_artifact_envelope(
        raw_payload,
        envelope_type="tester_output",
        artifact_role="verifier",
        task_path=str(task_path or ""),
        attempt_count=max(1, retry_count_observed + 1),
        summary=summary,
        role_outcome=raw_payload["role_outcome"],
        proposed_next_role=next_role,
        handoff_reason="repair_route_selected",
        handoff_summary=summary,
        handoff_instructions="Use the selected repair strategy without widening the bounded one-task claim.",
        verifier_verdict=verifier_verdict if verifier_verdict in {"pass", "fail", "blocked"} else "not_run",
        focused_result_count=len(focused_replay_commands),
        full_result_count=len(broad_replay_commands),
    )
    raw_payload["artifact_envelope"] = envelope
    return raw_payload


__all__ = ["select_single_task_targeted_repair"]
