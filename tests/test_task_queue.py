from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _task_queue_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return importlib.import_module("agents.lib.task_queue")


def _manifest_planner_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return importlib.import_module("agents.lib.manifest_planner")


def _batch_state_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return importlib.import_module("agents.lib.batch_state")


def _controller_contract_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return importlib.import_module("agents.lib.controller_contract")


def _multi_agent_loop_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return importlib.import_module("agents.lib.multi_agent_loop")


def _batch_executor_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return importlib.import_module("agents.lib.batch_executor")


def _run_task_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return importlib.import_module("agents.run_task")


def _write_task(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# task\n", encoding="utf-8")


def test_batch_executor_advances_two_accepted_tasks(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)

    persisted: list[dict[str, object]] = []

    def execute_task(item):
        return {"task_path": item.task_path}

    def validator(_item, _result):
        return True, "ok"

    def acceptance(_item, _result, _ok, _note):
        return {"acceptance_decision": "accepted", "note": "accepted"}

    def retry(_item, result, _retry_count):
        return result

    final_state, outcomes, final_decision = be.execute_batch_loop(
        initial_state=state,
        queue=queue,
        execute_task=execute_task,
        run_authoritative_validation=validator,
        run_final_acceptance_review=acceptance,
        self_heal_and_retry=retry,
        retry_budget=1,
        persist_state=lambda s: persisted.append(s.to_dict()),
    )

    assert final_state.batch_status == "completed"
    assert final_decision == "continue"
    assert len(outcomes) == 2
    assert all(outcome["acceptance_decision"] == "accepted" for outcome in outcomes)
    assert persisted[-1]["batch_status"] == "completed"


def test_batch_executor_stops_on_manual_or_blocked(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)

    def execute_task(item):
        return {"task_path": item.task_path}

    def validator(_item, _result):
        return True, "ok"

    def acceptance(item, _result, _ok, _note):
        if item.task_path.endswith("001.md"):
            return {"acceptance_decision": "manual_patch", "note": "needs manual patch"}
        return {"acceptance_decision": "accepted", "note": "accepted"}

    def retry(_item, result, _retry_count):
        return result

    final_state, outcomes, final_decision = be.execute_batch_loop(
        initial_state=state,
        queue=queue,
        execute_task=execute_task,
        run_authoritative_validation=validator,
        run_final_acceptance_review=acceptance,
        self_heal_and_retry=retry,
        retry_budget=1,
        persist_state=lambda _s: None,
    )

    assert final_state.batch_status in {"manual_patch_required", "blocked", "failed"}
    assert final_decision in {"manual_patch", "blocked", "stop"}
    assert any(outcome["acceptance_decision"] in {"manual_patch", "blocked"} for outcome in outcomes)


def test_single_task_default_selector_picks_first_ready(tmp_path: Path) -> None:
    tq = _task_queue_module()

    # Ready + blocked path
    ready = tmp_path / "tasks" / "001_ready.md"
    blocked = tmp_path / "tasks" / "002_blocked.md"
    _write_task(ready)

    manifest = {"tasks": [ready.as_posix(), blocked.as_posix()]}
    selection = tq.select_single_admissible_safe_task(manifest, repo_root=tmp_path)

    assert selection["default_single_task_path"] is True
    assert selection["widening_to_multi_task_forbidden"] is True
    assert selection["selected_task_path"].endswith("001_ready.md")
    assert selection["ready_task_paths"] == [selection["selected_task_path"]]
    assert blocked.as_posix() in selection["blocked_task_paths"]


def test_two_task_gate_snapshot_and_evaluation() -> None:
    run_task = _run_task_module()

    snap = run_task.two_task_readiness_gate_snapshot()
    assert snap["gate_enabled"] is True
    assert snap["default_single_task_path"] is True
    assert "ready_to_be_default" in snap["pilot_ready_verdicts"]
    assert "conditionally_ready_under_supervision" in snap["pilot_ready_verdicts"]
    assert snap["bounded_two_task_limit"] == 2
    assert snap["widening_to_general_multi_task_forbidden"] is True

    # Not allowed without operator flag
    eval1 = run_task.evaluate_two_task_readiness_gate(promotion_verdict="ready_to_be_default", operator_pilot_flag=False)
    assert eval1["allowed"] is False
    assert "missing_explicit_operator_flag" in eval1["preconditions"]

    # Allowed with operator flag and qualifying verdict, bounded to 2
    eval2 = run_task.evaluate_two_task_readiness_gate(
        promotion_verdict="ready_to_be_default",
        operator_pilot_flag=True,
        bounded_limit_requested=5,
    )
    assert eval2["allowed"] is True
    assert eval2["bounded"] is True
    assert eval2["bounded_limit"] == 2  # hard cap


def test_two_task_phase_transition_plans_conservatively() -> None:
    run_task = _run_task_module()

    rejected = {"allowed": False}
    hold = run_task.plan_two_task_phase_transition(current_phase="single_task_default", evaluation=rejected)
    assert hold["transition_allowed"] is False
    assert hold["next_phase"] == "single_task_default"

    accepted = {"allowed": True, "bounded_limit": 2}
    go = run_task.plan_two_task_phase_transition(current_phase="single_task_default", evaluation=accepted)
    assert go["transition_allowed"] is True
    assert go["next_phase"] == "two_task_pilot"
    assert go["bounded_limit"] == 2


def test_two_task_pilot_ineligible_when_promotion_verdict_below_required() -> None:
    run_task = _run_task_module()

    payload = {
        "verdict": "not_ready",
        "metrics": {
            "supervised_rate": 0.02,
            "authority_ambiguity_rate": 0.0,
            "compatibility_regressions": False,
        },
        "thresholds": {
            "max_supervised_rate": 0.10,
            "max_authority_ambiguity_rate": 0.05,
        },
    }
    ev = run_task.evaluate_two_task_readiness_gate(operator_pilot_flag=True, promotion_payload=payload)
    assert ev["allowed"] is False
    assert "verdict_below_threshold" in ev["reasons"]


def test_two_task_pilot_ineligible_when_rates_above_ceiling() -> None:
    run_task = _run_task_module()

    # Supervised rate above threshold
    payload = {
        "verdict": "ready_to_be_default",
        "metrics": {
            "supervised_rate": 0.20,
            "authority_ambiguity_rate": 0.00,
            "compatibility_regressions": False,
        },
        "thresholds": {
            "max_supervised_rate": 0.10,
            "max_authority_ambiguity_rate": 0.05,
        },
    }
    ev = run_task.evaluate_two_task_readiness_gate(operator_pilot_flag=True, promotion_payload=payload)
    assert ev["allowed"] is False
    assert "supervised_rate_above_threshold" in ev["reasons"]

    # Authority ambiguity above threshold
    payload2 = {
        "verdict": "ready_to_be_default",
        "metrics": {
            "supervised_rate": 0.00,
            "authority_ambiguity_rate": 0.10,
            "compatibility_regressions": False,
        },
        "thresholds": {
            "max_supervised_rate": 0.10,
            "max_authority_ambiguity_rate": 0.05,
        },
    }
    ev2 = run_task.evaluate_two_task_readiness_gate(operator_pilot_flag=True, promotion_payload=payload2)
    assert ev2["allowed"] is False
    assert "authority_ambiguity_rate_above_threshold" in ev2["reasons"]


def test_two_task_pilot_blocked_on_compatibility_regressions_even_if_verdict_qualifies() -> None:
    run_task = _run_task_module()

    payload = {
        "verdict": "ready_to_be_default",
        "metrics": {
            "supervised_rate": 0.00,
            "authority_ambiguity_rate": 0.00,
            "compatibility_regressions": True,
        },
        "thresholds": {
            "max_supervised_rate": 0.10,
            "max_authority_ambiguity_rate": 0.05,
        },
    }
    ev = run_task.evaluate_two_task_readiness_gate(operator_pilot_flag=True, promotion_payload=payload)
    assert ev["allowed"] is False
    assert "compatibility_regressions_block" in ev["reasons"]


def test_two_task_operator_flag_and_hard_cap_remain_in_force() -> None:
    run_task = _run_task_module()

    payload = {
        "verdict": "ready_to_be_default",
        "metrics": {
            "supervised_rate": 0.01,
            "authority_ambiguity_rate": 0.01,
            "compatibility_regressions": False,
        },
        "thresholds": {
            "max_supervised_rate": 0.10,
            "max_authority_ambiguity_rate": 0.05,
        },
    }

    # Missing operator flag blocks
    blocked = run_task.evaluate_two_task_readiness_gate(operator_pilot_flag=False, promotion_payload=payload)
    assert blocked["allowed"] is False
    assert "missing_explicit_operator_flag" in blocked["preconditions"]

    # With flag, hard cap at 2 remains enforced even if higher requested
    allowed = run_task.evaluate_two_task_readiness_gate(
        operator_pilot_flag=True,
        promotion_payload=payload,
        bounded_limit_requested=99,
    )
    assert allowed["allowed"] is True
    assert allowed["bounded_limit"] == 2
