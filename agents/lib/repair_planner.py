from __future__ import annotations

from typing import Any, Mapping


def _coerce_str_list(value: object) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw in value or ():  # type: ignore[arg-type]
        text = str(raw or "").strip()
        if text and text not in seen:
            items.append(text)
            seen.add(text)
    return items


def _preferred_lint_commands(*commands: str) -> list[str]:
    selected = [command for command in commands if "ruff check" in command]
    return selected[:2]


def build_single_task_repair_plan(
    *,
    task_path: str,
    verifier_artifact: Mapping[str, Any] | None = None,
    baseline_repair_artifact: Mapping[str, Any] | None = None,
    failure_taxonomy: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    verifier = dict(verifier_artifact or {})
    baseline = dict(baseline_repair_artifact or {})
    taxonomy = dict(failure_taxonomy or {})

    focused = _coerce_str_list(
        baseline.get("focused_replay_commands")
        or verifier.get("focused_results")
        or taxonomy.get("focused_replay_commands")
        or []
    )
    broad = _coerce_str_list(
        baseline.get("broad_replay_commands")
        or verifier.get("full_results")
        or taxonomy.get("broad_replay_commands")
        or []
    )
    target_paths = _coerce_str_list(taxonomy.get("evidence_paths") or taxonomy.get("required_paths") or [])
    failure_family = str(taxonomy.get("failure_family") or "").strip()
    selected_replay_commands = list(focused or broad)

    if not bool(baseline.get("repair_required", False)):
        strategy = "no_repair_required"
        lane = "none"
        next_role = "controller"
        repair_attempt_selected = False
        escalation_required = False
        route_rationale = "Verifier passed, so no self-heal plan is required."
        generic_replay_avoided = True
    elif bool(baseline.get("repair_budget_exhausted", False)) or bool(baseline.get("escalation_required", False)):
        strategy = "supervised_escalation"
        lane = "supervised_recovery"
        next_role = "operator"
        repair_attempt_selected = False
        escalation_required = True
        route_rationale = "The bounded repair budget is exhausted, so the one-task lane must escalate honestly."
        generic_replay_avoided = True
    elif failure_family == "incomplete_deliverable_coverage":
        strategy = "deliverable_coverage_patch_then_focused_replay"
        lane = "developer_repair"
        next_role = "builder"
        repair_attempt_selected = True
        escalation_required = False
        route_rationale = str(taxonomy.get("self_heal_reason") or "")
        generic_replay_avoided = True
    elif failure_family == "missing_file_updates":
        strategy = "required_path_patch_then_focused_replay"
        lane = "developer_repair"
        next_role = "builder"
        repair_attempt_selected = True
        escalation_required = False
        route_rationale = str(taxonomy.get("self_heal_reason") or "")
        generic_replay_avoided = True
    elif failure_family == "import_collection_error":
        strategy = "focused_import_collection_repair"
        lane = "developer_repair"
        next_role = "builder"
        repair_attempt_selected = True
        escalation_required = False
        route_rationale = str(taxonomy.get("self_heal_reason") or "")
        generic_replay_avoided = True
    elif failure_family == "formatting_lint_only":
        strategy = "lint_only_repair_then_replay"
        lane = "developer_repair"
        next_role = "builder"
        repair_attempt_selected = True
        escalation_required = False
        lint_commands = _preferred_lint_commands(*(focused + broad))
        selected_replay_commands = lint_commands or ["ruff check ."]
        route_rationale = str(taxonomy.get("self_heal_reason") or "")
        generic_replay_avoided = True
    elif failure_family == "test_regression":
        strategy = "focused_test_regression_repair"
        lane = "developer_repair"
        next_role = "builder"
        repair_attempt_selected = True
        escalation_required = False
        route_rationale = str(taxonomy.get("self_heal_reason") or "")
        generic_replay_avoided = True
    else:
        strategy = str(baseline.get("repair_strategy") or "focused_replay_then_targeted_patch")
        lane = str(baseline.get("remediation_lane") or "developer_repair")
        next_role = str(baseline.get("next_role") or "builder")
        repair_attempt_selected = bool(baseline.get("repair_attempt_selected", False))
        escalation_required = bool(baseline.get("escalation_required", False))
        route_rationale = (
            str(taxonomy.get("self_heal_reason") or "")
            or str(baseline.get("route_rationale") or "")
            or "The failure did not match a specific external-safe taxonomy family, so the router kept the baseline bounded repair path."
        )
        generic_replay_avoided = False

    plan = dict(baseline)
    plan.update(
        {
            "task_path": str(task_path or ""),
            "repair_strategy": strategy,
            "remediation_lane": lane,
            "next_role": next_role,
            "repair_attempt_selected": repair_attempt_selected,
            "escalation_required": escalation_required,
            "route_rationale": route_rationale,
            "focused_replay_commands": list(selected_replay_commands),
            "broad_replay_commands": list(broad),
            "selected_replay_commands": list(selected_replay_commands),
            "target_paths": list(target_paths),
            "failure_family": failure_family or "unknown",
            "failure_category": str(taxonomy.get("failure_category") or ""),
            "self_heal_lane": str(taxonomy.get("self_heal_lane") or lane),
            "smallest_credible_action": str(taxonomy.get("smallest_credible_action") or ""),
            "taxonomy_confidence": str(taxonomy.get("confidence") or ""),
            "matched_signals": _coerce_str_list(taxonomy.get("matched_signals")),
            "generic_replay_avoided": generic_replay_avoided,
            "explicit_evidence": {
                "required_paths": _coerce_str_list(taxonomy.get("required_paths")),
                "evidence_paths": _coerce_str_list(taxonomy.get("evidence_paths")),
                "failing_test_files": _coerce_str_list(taxonomy.get("failing_test_files")),
                "failing_test_nodes": _coerce_str_list(taxonomy.get("failing_test_nodes")),
            },
        }
    )
    return plan


__all__ = ["build_single_task_repair_plan"]
