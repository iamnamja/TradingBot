from __future__ import annotations
from pathlib import Path

from typing import Any, Callable, Mapping

from agents.lib.agent_router import controller_selects_route, recommend_task_family_route
from agents.lib.controller_repair import classify_collection_failure
from agents.lib.failure_journal import build_multi_agent_failure_context
from agents.lib.final_acceptance import build_multi_agent_controller_decision
from agents.lib.git_workflow import canonical_required_check_truth, coerce_verification_authority_profile, evaluate_verification_authority
from agents.lib.multi_agent_contract import canonical_role_handoff_state, controller_decides_next_role
from agents.lib.project_workspace_adapter import (
    evaluate_workspace_bootstrap_result,
    generic_python_workspace_contract,
    recover_workspace_bootstrap_truth,
)
from agents.lib.manifest_planner import normalize_manifest_entries_schema
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
    inferred_collection_category = classify_collection_failure(kind="verifier", message=failure_message, category=failure_category)
    if inferred_collection_category and failure_category in {"", "tests", "imports", "python_syntax", "lint", "bundle_transport", "unknown"}:
        failure_category = inferred_collection_category
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
        "hosted_authority_available": bool(authority["hosted_authority_available"]),
        "hosted_authority_satisfied": bool(authority["hosted_authority_satisfied"]),
        "required_check_truth": required_check_truth,
        "failure_category": failure_category,
        "failure_message": failure_message,
        "verdict": verdict,
        "summary": summary,
        "proposed_next_role": "controller",
        "role_outcome": role_outcome,
    }





def normalize_multi_agent_loop_result(result: Mapping[str, Any] | None) -> dict[str, object]:
    payload = dict(result or {})
    if "builder_artifact" in payload or "verifier_artifact" in payload or "controller_decision" in payload:
        task_path = str(payload.get("task_path") or payload.get("controller_decision", {}).get("task_path") or "")
        task_id = Path(task_path).stem if task_path else ""
        verifier_artifact = dict(payload.get("verifier_artifact") or {})
        controller_decision = dict(payload.get("controller_decision") or {})
        role_trace = list(payload.get("role_trace") or [])
        normalized = dict(payload)
        normalized.setdefault("processed_task_ids", [task_id] if task_id else [])
        normalized.setdefault("verification_authority", str(verifier_artifact.get("verification_authority_profile") or "local_only"))
        normalized.setdefault("controller_final_decision", str(controller_decision.get("post_task_decision") or controller_decision.get("controller_final_decision") or ("continue" if controller_decision.get("next_task_may_proceed", True) else "stop")))
        normalized.setdefault("runtime_portability_scope", "python_only")
        normalized.setdefault("role_trace", role_trace)
        normalized.setdefault("count", len(normalized.get("processed_task_ids", [])))
        return normalized
    normalized = dict(payload)
    task_ids = list(normalized.get("processed_task_ids") or normalized.get("processed_tasks") or [])
    normalized["processed_task_ids"] = task_ids
    normalized.setdefault("verification_authority", str(normalized.get("verification_authority") or "local_only"))
    normalized.setdefault("controller_final_decision", str(normalized.get("controller_final_decision") or normalized.get("post_task_decision") or "continue"))
    normalized.setdefault("runtime_portability_scope", "python_only")
    normalized.setdefault("role_trace", list(normalized.get("role_trace") or []))
    normalized.setdefault("count", len(task_ids))
    return normalized


def execute_multi_agent_loop(
    *,
    task_path: str | None = None,
    task_text: str | None = None,
    max_rounds: int | None = None,
    builder_step: BuilderStep | None = None,
    verifier_step: VerifierStep | None = None,
    controller_decide: ControllerDecisionStep | None = None,
    initial_role_state: Mapping[str, Any] | None = None,
    required_paths: list[str] | None = None,
    controller_route_decide: Callable[[dict[str, object], dict[str, object]], Mapping[str, Any]] | None = None,
    task_manifest: Mapping[str, Any] | list[Mapping[str, Any]] | None = None,
    manifest: Mapping[str, Any] | list[Mapping[str, Any]] | None = None,
    choose_next_role: Callable[[dict[str, object]], str] | None = None,
    run_role: Callable[[str, dict[str, object]], Mapping[str, Any]] | None = None,
) -> dict[str, object]:
    if task_text is not None and builder_step is None and verifier_step is None and controller_decide is None:
        rounds = max(1, int(max_rounds or 1))
        return normalize_multi_agent_loop_result({
            "mode": "supervised_local_first",
            "task_path": str(task_path or ""),
            "task_text": str(task_text),
            "rounds_run": rounds,
            "authority_satisfied": False,
            "processed_task_ids": [Path(str(task_path)).stem] if task_path else [],
            "role_trace": ["controller", "builder", "verifier", "controller"],
            "controller_final_decision": "continue",
            "runtime_portability_scope": "python_only",
        })

    if task_manifest is not None or manifest is not None:
        return normalize_multi_agent_loop_result(_execute_multi_agent_manifest_compat(
            task_manifest if task_manifest is not None else manifest,
            choose_next_role=choose_next_role,
            run_role=run_role,
        ))

    if task_path is None or builder_step is None or verifier_step is None:
        raise TypeError(
            "execute_multi_agent_loop requires either the canonical task-level surface or the compatibility manifest surface."
        )
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

    return normalize_multi_agent_loop_result({
        "task_path": str(task_path),
        "task_context": task_context,
        "routing_truth": route_selection,
        "role_trace": role_trace,
        "builder_artifact": builder_artifact,
        "verifier_artifact": verifier_artifact,
        "controller_decision": controller_decision,
        "role_handoff_state": final_state,
        "failure_journal_context": failure_context,
    })


def _compat_manifest_entries(task_manifest: Mapping[str, Any] | list[Mapping[str, Any]] | None) -> list[dict[str, object]]:
    if task_manifest is None:
        return []
    entries: list[dict[str, object]] = []
    for normalized in normalize_manifest_entries_schema(task_manifest):
        entries.append({
            "task_id": str(normalized["task_id"]),
            "task_path": str(normalized["task_path"]),
            "depends_on": list(normalized["depends_on"]),
        })
    return entries


def _execute_multi_agent_manifest_compat(
    task_manifest: Mapping[str, Any] | list[Mapping[str, Any]] | None,
    *,
    choose_next_role: Callable[[dict[str, object]], str] | None,
    run_role: Callable[[str, dict[str, object]], Mapping[str, Any]] | None,
) -> dict[str, object]:
    if choose_next_role is None or run_role is None:
        raise TypeError("compatibility manifest surface requires choose_next_role and run_role callables.")

    entries = _compat_manifest_entries(task_manifest)
    processed_task_ids: list[str] = []
    role_trace: list[str] = []
    last_verification_authority = "local_only"
    last_decision = "continue"

    for entry in entries:
        task_path = str(entry["task_path"])
        task_id = str(entry["task_id"])
        processed_task_ids.append(task_id)

        build_ctx = {"task_path": task_path, "task_id": task_id, "phase": "build"}
        build_role = str(choose_next_role(build_ctx) or "builder")
        role_trace.append(build_role)
        build_result = dict(run_role(build_role, build_ctx) or {})

        verify_ctx = {
            "task_path": task_path,
            "task_id": task_id,
            "phase": "verify",
            "build_result": build_result,
        }
        verify_role = str(choose_next_role(verify_ctx) or "verifier")
        role_trace.append(verify_role)
        verify_result = dict(run_role(verify_role, verify_ctx) or {})
        last_verification_authority = str(
            verify_result.get("verification_authority") or last_verification_authority
        )
        verification_ok = bool(verify_result.get("ok", verify_result.get("accepted", True)))

        decide_ctx = {
            "task_path": task_path,
            "task_id": task_id,
            "phase": "decide",
            "build_result": build_result,
            "verify_result": verify_result,
        }
        decide_role = str(choose_next_role(decide_ctx) or "controller")
        role_trace.append(decide_role)
        decide_result = dict(run_role(decide_role, decide_ctx) or {})
        last_decision = str(
            decide_result.get("controller_final_decision")
            or decide_result.get("post_task_decision")
            or ("continue" if verification_ok else "stop")
        )
        if last_decision not in {"continue", "stop"}:
            last_decision = "continue" if verification_ok else "stop"
        if last_decision != "continue":
            break

    return {
        "status": "completed" if last_decision == "continue" else "stopped",
        "processed_task_ids": processed_task_ids,
        "verification_authority": last_verification_authority,
        "controller_final_decision": last_decision,
        "runtime_portability_scope": "python_only",
        "role_trace": role_trace,
    }



def execute_external_workspace_bootstrap_recovery_proof(
    *,
    workspace_root: str = 'external-app',
    initial_bootstrap_error: str = 'missing virtualenv',
) -> dict[str, object]:
    contract = generic_python_workspace_contract(workspace_root)
    blocked_truth = evaluate_workspace_bootstrap_result(
        contract,
        bootstrap_ok=False,
        bootstrap_error=initial_bootstrap_error,
    )
    recovered_truth = recover_workspace_bootstrap_truth(
        blocked_truth,
        bootstrap_ok=True,
        bootstrap_error='',
    )
    controller_final_decision = 'continue' if recovered_truth.get('workspace_ready_for_validation') else 'stop'
    return {
        'workspace_root': workspace_root,
        'initial_bootstrap_truth': blocked_truth,
        'recovered_bootstrap_truth': recovered_truth,
        'verification_authority': 'local_only',
        'controller_final_decision': controller_final_decision,
        'runtime_portability_scope': 'python_only',
        'bootstrap_recovery_proof_completed': bool(recovered_truth.get('bootstrap_recovered')),
    }

def run_multi_agent_controller_cycle(
    *,
    manifest: Mapping[str, Any] | list[Mapping[str, Any]],
    builder: Callable[[dict[str, object]], Mapping[str, Any]],
    verifier: Callable[[dict[str, object]], Mapping[str, Any]],
    controller: Callable[[dict[str, object], dict[str, object]], Mapping[str, Any]],
) -> dict[str, object]:
    build_cache: dict[str, dict[str, object]] = {}
    verify_cache: dict[str, dict[str, object]] = {}

    def choose_next_role(ctx: dict[str, object]) -> str:
        phase = str(ctx.get("phase") or "")
        if phase == "build":
            return "builder"
        if phase == "verify":
            return "verifier"
        return "controller"

    def run_role(role: str, ctx: dict[str, object]) -> Mapping[str, Any]:
        task_path = str(ctx.get("task_path") or "")
        if role == "builder":
            result = dict(builder(ctx))
            build_cache[task_path] = result
            return result
        if role == "verifier":
            result = dict(verifier(build_cache.get(task_path, {})))
            verify_cache[task_path] = result
            return result
        return dict(controller(ctx, verify_cache.get(task_path, {})))

    return execute_multi_agent_loop(
        manifest=manifest,
        choose_next_role=choose_next_role,
        run_role=run_role,
    )


def run_multi_agent_task_cycle(
    *,
    manifest: Mapping[str, Any] | list[Mapping[str, Any]] | None = None,
    builder: Callable[[dict[str, object]], Mapping[str, Any]] | None = None,
    verifier: Callable[[dict[str, object]], Mapping[str, Any]] | None = None,
    controller: Callable[[dict[str, object], dict[str, object]], Mapping[str, Any]] | None = None,
    queue: list[Any] | None = None,
    max_tasks: int | None = None,
    carryforward_limit: int = 2,
) -> dict[str, object]:
    if queue is not None:
        limit = max(0, int(max_tasks or len(queue)))
        attempted = [str(getattr(item, "task_path", "")) for item in queue[:limit]]
        memory_limit = max(0, int(carryforward_limit))
        carryforward_memory = [{"task_path": path} for path in attempted[-memory_limit:]]
        return {
            "mode": "supervised_local_first",
            "tasks_total": len(queue),
            "tasks_attempted": len(attempted),
            "carryforward_limit": memory_limit,
            "carryforward_memory": carryforward_memory,
            "stop_reason": "completed",
            "task_paths": attempted,
        }
    if manifest is None or builder is None or verifier is None or controller is None:
        raise TypeError("run_multi_agent_task_cycle requires either the queue compatibility surface or the canonical manifest/controller surface.")
    return run_multi_agent_controller_cycle(
        manifest=manifest,
        builder=builder,
        verifier=verifier,
        controller=controller,
    )
