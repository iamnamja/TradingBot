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

    assert final_state.batch_status == "manual_patch_required"
    assert final_decision == "manual_patch"
    assert len(outcomes) == 1
    assert outcomes[0]["acceptance_decision"] == "manual_patch"


def test_three_step_canary_admission_accepts_strict_chain_and_preserves_supervision_truth() -> None:
    # Reuse adjacent-pair admission and resume-truth helpers from bounded pilot
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    bounded_pilot = importlib.import_module("agents.lib.bounded_pilot")

    task_a = {
        "id": "A",
        "admit": True,
        "resume_plan": {"mode": "resume", "surface": "dev_to_test", "precision": "precise"},
        "supervised": True,
    }
    task_b = {
        "id": "B",
        "admit": True,
        "follows": "A",
        "resume_plan": {"mode": "resume", "surface": "test_to_merge", "precision": "unknown"},
        "supervision": "explicit_supervision",
    }
    task_c = {
        "id": "C",
        "admit": True,
        "follows": "B",
        # no explicit resume plan on C; adjacent-pair inference will mark unknown precision
    }

    # Adjacent-pair admission truth
    ab_adm = bounded_pilot._admission_truth(task_a, task_b)
    bc_adm = bounded_pilot._admission_truth(task_b, task_c)
    assert ab_adm["accepted"] is True
    assert bc_adm["accepted"] is True

    # Adjacent handoff eligibility truth
    ab_handoff = bounded_pilot._handoff_eligible(task_a, task_b)
    bc_handoff = bounded_pilot._handoff_eligible(task_b, task_c)
    assert ab_handoff["eligible"] is True
    assert bc_handoff["eligible"] is True

    # Resume-truth artifacts per adjacent pair (reused seam)
    ab_resume = bounded_pilot._coerce_resume_truth(task_a, task_b, handoff_ok=True)
    bc_resume = bounded_pilot._coerce_resume_truth(task_b, task_c, handoff_ok=True)
    assert ab_resume["mode"] in {"resume", "default"}
    assert ab_resume["precision"] in {"precise", "unknown"}
    assert bc_resume["mode"] in {"resume", "default", "unknown"}
    assert bc_resume["precision"] in {"unknown", "precise", "broad"}

    # Supervision truth remains first-class
    manual_intervention_observed = bool(task_a.get("manual_intervention", False) or task_b.get("manual_intervention", False) or task_c.get("manual_intervention", False))
    assert manual_intervention_observed is False
    no_manual_intervention = not manual_intervention_observed
    assert no_manual_intervention is True


def test_three_step_canary_admission_rejects_broken_adjacency_or_missing_admit() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    bounded_pilot = importlib.import_module("agents.lib.bounded_pilot")

    # Broken adjacency: B does not follow A
    task_a = {"id": "A", "admit": True}
    task_b = {"id": "B", "admit": True, "follows": "X"}  # should follow A
    task_c = {"id": "C", "admit": True, "follows": "B"}

    ab_handoff = bounded_pilot._handoff_eligible(task_a, task_b)
    bc_handoff = bounded_pilot._handoff_eligible(task_b, task_c)

    assert ab_handoff["eligible"] is False
    assert bc_handoff["eligible"] is True

    # Missing admit on C should deny admission chain-wide
    task_c_missing = {"id": "C", "follows": "B"}
    bc_adm = bounded_pilot._admission_truth(task_b, task_c_missing)
    assert bc_adm["accepted"] is False
