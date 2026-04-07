from __future__ import annotations

from typing import Any, Mapping

from agents.lib.multi_agent_contract import controller_decides_next_role

TASK_FAMILIES: tuple[str, ...] = (
    "builder_first",
    "verifier_first",
    "proof_docs",
    "bootstrap_setup",
    "strict_manual_controller_core",
)

ROUTING_LANES: tuple[str, ...] = (
    "builder",
    "verifier",
    "proof_docs",
    "bootstrap_setup",
    "constrained_manual",
)


def canonical_task_family_route(payload: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, object]:
    data = dict(payload or {})
    data.update(overrides)
    task_family = str(data.get("task_family") or "builder_first").strip()
    if task_family not in TASK_FAMILIES:
        task_family = "builder_first"
    recommended_next_role = str(data.get("recommended_next_role") or "builder").strip()
    if recommended_next_role not in {"controller", "builder", "verifier", "manual_patch", "blocked", "stop"}:
        recommended_next_role = "builder"
    recommended_lane = str(data.get("recommended_lane") or "builder").strip()
    if recommended_lane not in ROUTING_LANES:
        recommended_lane = "builder"
    return {
        "task_family": task_family,
        "recommended_next_role": recommended_next_role,
        "recommended_lane": recommended_lane,
        "strict_mode_required": bool(data.get("strict_mode_required", False)),
        "controller_may_override": bool(data.get("controller_may_override", True)),
        "resume_safe": bool(data.get("resume_safe", True)),
        "route_rationale": str(data.get("route_rationale") or ""),
        "controller_selected_next_role": str(data.get("controller_selected_next_role") or recommended_next_role),
        "controller_selected_lane": str(data.get("controller_selected_lane") or recommended_lane),
        "manual_lane_required": bool(data.get("manual_lane_required", False)),
        "blocked": bool(data.get("blocked", False)),
        "task_admission_lane": str(data.get("task_admission_lane") or "supervised_autonomous"),
        "task_admission_rationale": str(data.get("task_admission_rationale") or ""),
        "protected_or_meta_task": bool(data.get("protected_or_meta_task", False)),
        "ambiguous_task_shape": bool(data.get("ambiguous_task_shape", False)),
        "bounded_decomposition_required": bool(data.get("bounded_decomposition_required", False)),
        "decomposition_status": str(data.get("decomposition_status") or "not_required"),
        "decomposition_unit_count": int(data.get("decomposition_unit_count", 0) or 0),
        "decomposition_summary": str(data.get("decomposition_summary") or ""),
        "decomposition_units": [dict(item) for item in data.get("decomposition_units") or [] if isinstance(item, Mapping)],
    }


def recommend_task_family_route(*, task_context: Mapping[str, Any] | None = None, current_role: str = "controller") -> dict[str, object]:
    context = dict(task_context or {})
    family = str(context.get("task_family") or "builder_first")
    admission_lane = str(context.get("task_admission_lane") or "supervised_autonomous")
    base = {
        "task_admission_lane": admission_lane,
        "task_admission_rationale": str(context.get("task_admission_rationale") or ""),
        "protected_or_meta_task": bool(context.get("protected_or_meta_task", False)),
        "ambiguous_task_shape": bool(context.get("ambiguous_task_shape", False)),
        "bounded_decomposition_required": bool(context.get("bounded_decomposition_required", False)),
        "decomposition_status": str(context.get("decomposition_status") or "not_required"),
        "decomposition_unit_count": int(context.get("decomposition_unit_count", 0) or 0),
        "decomposition_summary": str(context.get("decomposition_summary") or ""),
        "decomposition_units": [dict(item) for item in context.get("decomposition_units") or [] if isinstance(item, Mapping)],
    }
    rationale = base["task_admission_rationale"] or ""
    if rationale and base["decomposition_status"] != "not_required" and base["decomposition_summary"]:
        rationale = rationale + " " + str(base["decomposition_summary"])
    elif not rationale and base["decomposition_summary"] and base["decomposition_status"] != "not_required":
        rationale = str(base["decomposition_summary"])

    if admission_lane == "manual_only" or bool(base["protected_or_meta_task"]) or family == "strict_manual_controller_core":
        return canonical_task_family_route(
            task_family="strict_manual_controller_core",
            recommended_next_role="manual_patch",
            recommended_lane="constrained_manual",
            strict_mode_required=True,
            manual_lane_required=True,
            route_rationale=rationale or "Controller-core tasks remain constrained/manual and must not bypass strict-mode guardrails.",
            **base,
        )
    if family == "bootstrap_setup":
        return canonical_task_family_route(
            task_family=family,
            recommended_next_role="builder",
            recommended_lane="bootstrap_setup",
            route_rationale=rationale or "Bootstrap and workspace setup tasks should begin in the builder lane.",
            **base,
        )
    if family == "verifier_first":
        return canonical_task_family_route(
            task_family=family,
            recommended_next_role="verifier",
            recommended_lane="verifier",
            route_rationale=rationale or "Verification-only tasks can begin directly in the verifier lane.",
            **base,
        )
    if family == "proof_docs":
        return canonical_task_family_route(
            task_family=family,
            recommended_next_role="builder",
            recommended_lane="proof_docs",
            strict_mode_required=True,
            route_rationale=rationale or "Proof/docs tasks remain builder-driven but stay under proof-shaping guardrails.",
            **base,
        )
    return canonical_task_family_route(
        task_family="builder_first",
        recommended_next_role="builder",
        recommended_lane="builder",
        route_rationale=rationale or "Builder-first is the default route for code-building tasks.",
        **base,
    )


def controller_selects_route(
    route: Mapping[str, Any] | None,
    *,
    current_role: str = "controller",
    selected_next_role: str | None = None,
    selected_lane: str | None = None,
) -> dict[str, object]:
    canonical = canonical_task_family_route(route)
    requested_role = str(selected_next_role or canonical.get("recommended_next_role") or "builder")
    if requested_role in {"manual_patch", "blocked", "stop"}:
        decided_role = requested_role
    else:
        decided_role = controller_decides_next_role(
            current_role=current_role,
            proposed_next_role=requested_role,
            proposed_by_role="controller",
        )
    if selected_lane:
        decided_lane = str(selected_lane)
    else:
        decided_lane = str(canonical.get("recommended_lane") or "builder")
        if decided_role == "verifier":
            decided_lane = "verifier"
        elif decided_role in {"manual_patch", "blocked", "stop", "controller"}:
            decided_lane = "constrained_manual"
    return canonical_task_family_route(
        canonical,
        controller_selected_next_role=decided_role,
        controller_selected_lane=decided_lane,
        blocked=decided_role in {"blocked", "stop"},
    )


def format_task_family_route(route: Mapping[str, Any] | None) -> str:
    canonical = canonical_task_family_route(route)
    return (
        f"Task-family route: family={canonical['task_family']} "
        f"recommended={canonical['recommended_next_role']}({canonical['recommended_lane']}) "
        f"selected={canonical['controller_selected_next_role']}({canonical['controller_selected_lane']})"
    )



def canonical_targeted_repair_route(payload: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, object]:
    data = dict(payload or {})
    data.update(overrides)
    target_files = [str(item) for item in data.get("target_files") or [] if str(item)]
    return {
        "repair_strategy": str(data.get("repair_strategy") or "manual_stop"),
        "remediation_lane": str(data.get("remediation_lane") or "operator"),
        "targeted_patch_surface": str(data.get("targeted_patch_surface") or "broad_builder_repair"),
        "target_files": target_files,
        "prefer_minimal_patch": bool(data.get("prefer_minimal_patch", False)),
        "minimal_patch_selected": bool(data.get("minimal_patch_selected", False)),
        "max_files_to_edit": int(data.get("max_files_to_edit", len(target_files) or 0)),
        "route_rationale": str(data.get("route_rationale") or data.get("rationale") or ""),
    }


def recommend_targeted_repair_route(route: Mapping[str, Any] | None = None) -> dict[str, object]:
    canonical = canonical_targeted_repair_route(route)
    if canonical["remediation_lane"] == "builder" and canonical["prefer_minimal_patch"]:
        return canonical_targeted_repair_route(
            canonical,
            route_rationale=(canonical["route_rationale"] or "Prefer the smallest plausible repair surface before broader rewrites."),
        )
    return canonical
