from __future__ import annotations

from typing import Any, Callable, Mapping

from agents.lib.agent_router import controller_selects_route, recommend_task_family_route
from agents.lib.failure_journal import build_multi_agent_failure_context
from agents.lib.final_acceptance import build_multi_agent_controller_decision
from agents.lib.git_workflow import canonical_required_check_truth, coerce_verification_authority_profile, evaluate_verification_authority
from agents.lib.multi_agent_contract import canonical_role_handoff_state, controller_decides_next_role
from agents.lib.task_contracts import multi_agent_task_context


BuilderStep = Callable[[dict[str, object]], Mapping[str, Any]]
VerifierStep = Callable[[dict[str, object], dict[str, object]], Mapping[str, Any]]
ControllerDecisionStep = Callable[[dict[str, object], dict[str, object], dict[str, object]], Mapping[str, Any]]


def _coerce_changed_files(payload: Mapping[str, Any] | None) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for raw in (payload or {}).get("changed_files", []) or []:
        path = str(raw or "").strip().replace("\\", "/")
        if path and path not in seen:
            files.append(path)
            seen.add(path)
    return files


def build_builder_patch_attempt(*, task_path: str, attempt_count: int, result: Mapping[str, Any] | None) -> dict[str, object]:
    payload = dict(result or {})
    changed_files = _coerce_changed_files(payload)
    summary = str(payload.get("summary") or payload.get("note") or "").strip()
    if not summary:
        if changed_files:
            summary = f"Builder proposed patch touching {len(changed_files)} file(s)."
        else:
            summary = "Builder produced no material patch changes."
    outcome = "builder_patch_proposed" if changed_files or payload.get("bundle") or payload.get("patch") else "builder_noop"
    return {
        "role": "builder",
        "artifact_kind": "builder_patch_attempt",
        "task_path": str(task_path),
        "attempt_count": max(1, int(attempt_count or 1)),
        "changed_files": changed_files,
        "summary": summary,
        "output_summary": str(payload.get("output_summary") or summary),
        "proposed_next_role": "verifier",
        "role_outcome": outcome,
        "result": payload,
    }


def build_verifier_evidence_bundle(
    *,
    task_path: str,
    builder_artifact: Mapping[str, Any],
    verification: Mapping[str, Any] | None,
) -> dict[str, object]:
    payload = dict(verification or {})
    acceptance_report = dict(payload.get("acceptance_report") or {})
    if not acceptance_report:
        acceptance_report = {
            "acceptance_decision": str(payload.get("acceptance_decision") or "retryable_failure"),
            "post_task_decision": str(payload.get("post_task_decision") or "stop"),
            "next_task_may_proceed": bool(payload.get("next_task_may_proceed", False)),
            "note": str(payload.get("note") or payload.get("validator_note") or ""),
        }
    validator_ok = bool(payload.get("validator_ok", False))
    profile = coerce_verification_authority_profile(payload.get("verification_authority_profile"), default="local_only")
    required_check_truth = canonical_required_check_truth(
        payload.get("required_check_truth") if isinstance(payload.get("required_check_truth"), Mapping) else None,
        verification_authority_profile=profile,
        required_checks_discovered=payload.get("required_checks_discovered"),
        required_checks_missing=payload.get("required_checks_missing"),
        required_checks_pending=payload.get("required_checks_pending"),
        required_checks_timed_out=payload.get("required_checks_timed_out"),
        required_checks_failed=payload.get("required_checks_failed"),
        required_checks_passed=payload.get("required_checks_passed"),
        missing_required_checks_blocks_merge=payload.get("missing_required_checks_blocks_merge"),
    )
    authority = evaluate_verification_authority(
        verification_authority_profile=profile,
        local_validation_passed=validator_ok,
        required_check_truth=required_check_truth,
    )
    if str(acceptance_report.get("acceptance_decision") or "retryable_failure") == "accepted" and not bool(authority["verification_authority_satisfied"]):
        acceptance_report = dict(authority["controller_report"])
    validator_note = str(payload.get("validator_note") or acceptance_report.get("note") or "").strip()
    failure_category = str(payload.get("failure_category") or acceptance_report.get("failure_category") or ("ci_only_failure" if not bool(authority["verification_authority_satisfied"]) else "")).strip()
    failure_message = str(payload.get("failure_message") or payload.get("validator_note") or acceptance_report.get("note") or str(authority.get("summary") or "")).strip()
    acceptance_decision = str(acceptance_report.get("acceptance_decision") or "retryable_failure")
    if acceptance_decision == "accepted" and bool(authority["verification_authority_satisfied"]):
        verdict = "pass"
        role_outcome = "verification_passed"
    elif acceptance_decision == "blocked":
        verdict = "blocked"
        role_outcome = "verification_blocked"
    else:
        verdict = "fail"
        role_outcome = "verification_failed"
    summary = str(payload.get("summary") or "").strip()
    if not summary:
        if verdict == "pass":
            summary = "Verifier ran focused/full validation and produced authority-satisfying evidence."
        elif verdict == "blocked":
            summary = str(authority["summary"] or "Verifier produced blocked evidence requiring controller stop.")
        else:
            summary = "Verifier produced failing evidence for controller review."
    return {
        "role": "verifier",
        "artifact_kind": "verifier_evidence_bundle",
        "task_path": str(task_path),
        "builder_summary": str(builder_artifact.get("summary") or ""),
        "validator_ok": validator_ok,
        "validator_note": validator_note,
        "focused_results": list(payload.get("focused_results", []) or []),
        "full_results": list(payload.get("full_results", []) or []),
        "acceptance_report": acceptance_report,
        "verification_authority_profile": profile,
        "verification_authority_satisfied": bool(authority["verification_authority_satisfied"]),
        "required_check_truth": required_check_truth,
        "failure_category": failure_category,
        "failure_message": failure_message,
        "verdict": verdict,
        "summary": summary,
        "proposed_next_role": "controller",
        "role_outcome": role_outcome,
    }


def execute_multi_agent_loop(
    *,
    task_path: str,
    builder_step: BuilderStep,
    verifier_step: VerifierStep,
    controller_decide: ControllerDecisionStep | None = None,
    initial_role_state: Mapping[str, Any] | None = None,
    required_paths: list[str] | None = None,
    controller_route_decide: Callable[[dict[str, object], dict[str, object]], Mapping[str, Any]] | None = None,
) -> dict[str, object]:
    task_context = multi_agent_task_context(required_paths or [], controller_paths=None)
    route_recommendation = recommend_task_family_route(task_context=task_context, current_role="controller")
    route_selection = controller_selects_route(route_recommendation, current_role="controller")

    role_trace = ["controller"]
    controller_entry = canonical_role_handoff_state(
        initial_role_state,
        active_role="controller",
        handoff_reason=f"task_family:{route_selection['task_family']}",
        handoff_summary=str(route_selection.get("route_rationale") or "Controller owns next-role selection and final task authority."),
        handoff_instructions=f"Select the {route_selection['controller_selected_next_role']} role in the {route_selection['controller_selected_lane']} lane.",
        controller_next_role_decision=str(route_selection.get("controller_selected_next_role") or "builder"),
        role_outcome="controller_routed",
    )

    if controller_route_decide is not None:
        route_override = dict(controller_route_decide(dict(route_selection), dict(controller_entry)) or {})
        route_selection = controller_selects_route(
            route_selection,
            current_role="controller",
            selected_next_role=str(route_override.get("selected_next_role") or route_override.get("recommended_next_role") or route_selection.get("controller_selected_next_role") or "builder"),
            selected_lane=str(route_override.get("selected_lane") or route_override.get("recommended_lane") or route_selection.get("controller_selected_lane") or route_selection.get("recommended_lane") or "builder"),
        )
        controller_entry = canonical_role_handoff_state(
            controller_entry,
            handoff_reason=f"task_family:{route_selection['task_family']}",
            handoff_summary=str(route_override.get("summary") or route_selection.get("route_rationale") or ""),
            handoff_instructions=f"Select the {route_selection['controller_selected_next_role']} role in the {route_selection['controller_selected_lane']} lane.",
            controller_next_role_decision=str(route_selection.get("controller_selected_next_role") or "builder"),
        )

    selected_role = str(route_selection.get("controller_selected_next_role") or "builder")

    if selected_role in {"manual_patch", "blocked", "stop", "controller"}:
        controller_decision = {
            "role": "controller",
            "artifact_kind": "controller_decision",
            "task_path": str(task_path),
            "action": "stop",
            "acceptance_decision": "manual_patch" if selected_role == "manual_patch" else ("blocked" if selected_role == "blocked" else "retryable_failure"),
            "post_task_decision": "manual_patch" if selected_role == "manual_patch" else ("blocked" if selected_role == "blocked" else "stop"),
            "next_task_may_proceed": False,
            "verifier_verdict": "not_run",
            "builder_summary": "",
            "verifier_summary": "",
            "summary": str(route_selection.get("route_rationale") or "Controller kept the task in a constrained/manual lane."),
            "repair_strategy": "manual_constrained_lane",
            "remediation_lane": str(route_selection.get("controller_selected_lane") or "constrained_manual"),
            "route_rationale": str(route_selection.get("route_rationale") or ""),
            "final_authority_role": "controller",
            "handoff_reason": f"task_family:{route_selection['task_family']}",
            "instructions": "Stop honestly and wait for manual/controller-core handling before continuing.",
            "next_role_decision": selected_role,
            "routing_truth": dict(route_selection),
        }
        failure_context = build_multi_agent_failure_context(
            task_path=task_path,
            role_trace=role_trace,
            builder_artifact={},
            verifier_artifact={},
            controller_decision=controller_decision,
        )
        final_state = canonical_role_handoff_state(
            controller_entry,
            handoff_reason=f"task_family:{route_selection['task_family']}",
            handoff_summary=str(controller_decision.get("summary") or ""),
            handoff_instructions=str(controller_decision.get("instructions") or ""),
            role_output_summary=str(controller_decision.get("summary") or ""),
            controller_next_role_decision=str(controller_decision.get("next_role_decision") or selected_role),
        )
        return {
            "task_path": str(task_path),
            "task_context": task_context,
            "routing_truth": route_selection,
            "role_trace": role_trace,
            "builder_artifact": {},
            "verifier_artifact": {},
            "controller_decision": controller_decision,
            "role_handoff_state": final_state,
            "failure_journal_context": failure_context,
        }

    if selected_role == "verifier":
        builder_artifact = build_builder_patch_attempt(task_path=task_path, attempt_count=0, result={})
        verifier_state = canonical_role_handoff_state(
            controller_entry,
            active_role="verifier",
            prior_role="controller",
            role_attempt_count=int(controller_entry.get("role_attempt_count", 0)) + 1,
            handoff_reason=f"task_family:{route_selection['task_family']}",
            handoff_summary="Controller selected verifier-first routing for this task family.",
            handoff_instructions="Run focused validation first and produce a verifier evidence bundle.",
            controller_next_role_decision="verifier",
            role_outcome="controller_routed",
        )
        role_trace.append("verifier")
        verifier_result = dict(verifier_step(dict(builder_artifact), dict(verifier_state)))
        verifier_artifact = build_verifier_evidence_bundle(task_path=task_path, builder_artifact=builder_artifact, verification=verifier_result)
        final_controller_state = canonical_role_handoff_state(
            verifier_state,
            active_role="controller",
            prior_role="verifier",
            handoff_reason="verifier_completed",
            handoff_summary="Controller reviewed verifier evidence and made the final decision.",
            handoff_instructions="Decide whether to accept, repair, stop, or advance.",
            role_output_summary=str(verifier_artifact.get("summary") or ""),
            verifier_verdict=str(verifier_artifact.get("verdict") or "not_run"),
            controller_next_role_decision="controller",
            role_outcome=str(verifier_artifact.get("role_outcome") or "verification_failed"),
        )
        role_trace.append("controller")
    else:
        next_builder = controller_decides_next_role(current_role="controller", proposed_next_role="builder", proposed_by_role="controller")
        builder_state = canonical_role_handoff_state(
            controller_entry,
            active_role="builder",
            prior_role="controller",
            role_attempt_count=int(controller_entry.get("role_attempt_count", 0)) + 1,
            handoff_reason=f"task_family:{route_selection['task_family']}",
            handoff_summary=str(route_selection.get("route_rationale") or "Controller selected builder routing."),
            handoff_instructions="Produce a machine-readable patch/result bundle for verifier review.",
            controller_next_role_decision=next_builder,
            role_outcome="controller_routed",
        )
        role_trace.append("builder")
        builder_result = dict(builder_step(dict(builder_state)))
        builder_artifact = build_builder_patch_attempt(task_path=task_path, attempt_count=int(builder_state.get("role_attempt_count", 1)), result=builder_result)
        controller_after_builder = canonical_role_handoff_state(
            builder_state,
            active_role="controller",
            prior_role="builder",
            handoff_reason="builder_completed",
            handoff_summary="Controller reviewed builder output and routed verifier.",
            handoff_instructions="Choose verifier to validate the builder output.",
            role_output_summary=str(builder_artifact.get("summary") or ""),
            controller_next_role_decision="verifier",
            role_outcome=str(builder_artifact.get("role_outcome") or "builder_noop"),
        )
        role_trace.append("controller")
        next_verifier = controller_decides_next_role(current_role="controller", proposed_next_role="verifier", proposed_by_role="controller")
        verifier_state = canonical_role_handoff_state(
            controller_after_builder,
            active_role="verifier",
            prior_role="controller",
            role_attempt_count=int(builder_state.get("role_attempt_count", 1)) + 1,
            handoff_reason="controller_selected_verifier",
            handoff_summary="Verifier should run focused/full validation and summarize evidence.",
            handoff_instructions="Run focused validation first, then full validation as required. Produce a distinct evidence bundle.",
            role_output_summary=str(builder_artifact.get("summary") or ""),
            controller_next_role_decision=next_verifier,
            role_outcome="controller_routed",
        )
        role_trace.append("verifier")
        verifier_result = dict(verifier_step(dict(builder_artifact), dict(verifier_state)))
        verifier_artifact = build_verifier_evidence_bundle(task_path=task_path, builder_artifact=builder_artifact, verification=verifier_result)
        final_controller_state = canonical_role_handoff_state(
            verifier_state,
            active_role="controller",
            prior_role="verifier",
            handoff_reason="verifier_completed",
            handoff_summary="Controller reviewed verifier evidence and made the final decision.",
            handoff_instructions="Decide whether to accept, repair, stop, or advance.",
            role_output_summary=str(verifier_artifact.get("summary") or ""),
            verifier_verdict=str(verifier_artifact.get("verdict") or "not_run"),
            controller_next_role_decision="controller",
            role_outcome=str(verifier_artifact.get("role_outcome") or "verification_failed"),
        )
        role_trace.append("controller")

    decider = controller_decide or (lambda verifier, builder, state: build_multi_agent_controller_decision(verifier_artifact=verifier, builder_artifact=builder, role_state=state))
    controller_decision = dict(decider(dict(verifier_artifact), dict(builder_artifact), dict(final_controller_state)))
    controller_decision.setdefault("role", "controller")
    controller_decision.setdefault("artifact_kind", "controller_decision")
    controller_decision.setdefault("task_path", str(task_path))
    controller_decision.setdefault("final_authority_role", "controller")
    controller_decision.setdefault("role_trace", list(role_trace))
    controller_decision.setdefault("routing_truth", dict(route_selection))

    failure_context = build_multi_agent_failure_context(
        task_path=task_path,
        role_trace=role_trace,
        builder_artifact=builder_artifact,
        verifier_artifact=verifier_artifact,
        controller_decision=controller_decision,
    )

    final_state = canonical_role_handoff_state(
        final_controller_state,
        handoff_reason=f"task_family:{route_selection['task_family']}",
        handoff_summary=str(controller_decision.get("summary") or route_selection.get("route_rationale") or ""),
        handoff_instructions=str(controller_decision.get("instructions") or ""),
        role_output_summary=str(controller_decision.get("summary") or ""),
        controller_next_role_decision=str(controller_decision.get("next_role_decision") or "controller"),
    )

    return {
        "task_path": str(task_path),
        "task_context": task_context,
        "routing_truth": route_selection,
        "role_trace": role_trace,
        "builder_artifact": builder_artifact,
        "verifier_artifact": verifier_artifact,
        "controller_decision": controller_decision,
        "role_handoff_state": final_state,
        "failure_journal_context": failure_context,
    }
