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
    assert final_state.batch_status in {"manual_patch_required", "stopped"}
    assert final_decision in {"manual_patch", "blocked", "stop"}
    assert len(outcomes) == 1
    assert outcomes[0]["acceptance_decision"] == "manual_patch"


def test_short_ordinary_manifest_reproof_progresses_with_bounded_carryforward(tmp_path: Path) -> None:
    tq = _task_queue_module()
    loop = _multi_agent_loop_module()

    _write_task(tmp_path / "tasks" / "201.md")
    _write_task(tmp_path / "tasks" / "202.md")

    manifest = {
        "tasks": ["tasks/201.md", "tasks/202.md"],
        "max_tasks": 2,
    }
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    assert [item.task_path for item in queue] == ["tasks/201.md", "tasks/202.md"]

    result = loop.run_multi_agent_task_cycle(
        queue=queue,
        max_tasks=2,
        carryforward_limit=2,
    )

    assert result["mode"] == "supervised_local_first"
    assert result["tasks_total"] == 2
    assert result["tasks_attempted"] == 2
    assert result["carryforward_limit"] == 2
    assert len(result["carryforward_memory"]) <= 2
    assert result["stop_reason"] in {"completed", "authority_blocked", "admission_blocked"}



def test_dependency_aware_next_task_selection_prefers_ready_items() -> None:
    tq = _task_queue_module()
    planner = _manifest_planner_module()

    graph = planner.build_dependency_graph(
        {
            "tasks": [
                {"path": "tasks/001.md", "depends_on": []},
                {"path": "tasks/002.md", "depends_on": ["tasks/001.md"]},
                {"path": "tasks/003.md", "depends_on": []},
            ]
        }
    )
    queue = tq.build_task_queue_from_manifest(
        {"tasks": ["tasks/001.md", "tasks/002.md", "tasks/003.md"]},
        dependency_graph=graph,
    )

    first = tq.select_next_task(queue, completed_task_paths=[])
    assert first.task_path in {"tasks/001.md", "tasks/003.md"}

    second = tq.select_next_task(queue, completed_task_paths=["tasks/001.md"])
    assert second.task_path in {"tasks/002.md", "tasks/003.md"}


def test_task_136_dependency_aware_selection_returns_none_when_no_tasks_are_ready() -> None:
    tq = _task_queue_module()
    planner = _manifest_planner_module()

    graph = planner.build_dependency_graph(
        {
            "tasks": [
                {"path": "tasks/010.md", "depends_on": ["tasks/011.md"]},
                {"path": "tasks/011.md", "depends_on": ["tasks/010.md"]},
            ]
        }
    )
    queue = tq.build_task_queue_from_manifest(
        {"tasks": ["tasks/010.md", "tasks/011.md"]},
        dependency_graph=graph,
    )

    assert tq.select_next_task(queue, completed_task_paths=[]) is None



def test_plan_safe_lane_stop_requeue_policy_runs_one_safe_task_and_handoffs_supervised_mix() -> None:
    tq = _task_queue_module()
    queue = [
        tq.TaskQueueItem(task_path="tasks/201.md", ordinal=1),
        tq.TaskQueueItem(task_path="tasks/202.md", ordinal=2),
        tq.TaskQueueItem(task_path="tasks/203.md", ordinal=3, depends_on=("tasks/201.md",)),
    ]
    task_texts = {
        "tasks/201.md": "## Create or update these exact files\n- `tests/test_task_queue.py`\n",
        "tasks/202.md": "## Create or update these exact files\n- `agents/run_task.py`\n",
        "tasks/203.md": "## Create or update these exact files\n- `tests/test_single_task_runner.py`\n",
    }

    plan = tq.plan_safe_lane_stop_requeue_policy(
        queue,
        task_text_loader=lambda task_path: task_texts[task_path],
    )

    assert plan["decision"] == "run_one_and_stop"
    assert plan["selected_task_path"] == "tasks/201.md"
    assert plan["supervised_handoff_task_paths"] == ["tasks/202.md"]
    assert plan["requeue_task_paths"] == ["tasks/203.md"]
    assert plan["stop_after_selected"] is True
    assert plan["supervised_handoff_required"] is True



def test_plan_safe_lane_stop_requeue_policy_refuses_multiple_ready_safe_tasks() -> None:
    tq = _task_queue_module()
    queue = [
        tq.TaskQueueItem(task_path="tasks/301.md", ordinal=1),
        tq.TaskQueueItem(task_path="tasks/302.md", ordinal=2),
        tq.TaskQueueItem(task_path="tasks/303.md", ordinal=3),
    ]
    task_texts = {
        "tasks/301.md": "## Create or update these exact files\n- `tests/test_task_queue.py`\n",
        "tasks/302.md": "## Create or update these exact files\n- `tests/test_single_task_runner.py`\n",
        "tasks/303.md": "## Create or update these exact files\n- `agents/run_task.py`\n",
    }

    plan = tq.plan_safe_lane_stop_requeue_policy(
        queue,
        task_text_loader=lambda task_path: task_texts[task_path],
    )

    assert plan["decision"] == "stop_and_requeue"
    assert plan["selected_task_path"] == ""
    assert sorted(plan["ready_safe_task_paths"]) == ["tasks/301.md", "tasks/302.md"]
    assert plan["supervised_handoff_task_paths"] == ["tasks/303.md"]
    assert sorted(plan["requeue_task_paths"]) == ["tasks/301.md", "tasks/302.md"]



def test_execute_safe_lane_scheduler_mix_policy_routes_through_bridge(tmp_path: Path) -> None:
    tq = _task_queue_module()
    be = _batch_executor_module()
    queue = [
        tq.TaskQueueItem(task_path="tasks/601.md", ordinal=1),
        tq.TaskQueueItem(task_path="tasks/602.md", ordinal=2),
    ]
    task_texts = {
        "tasks/601.md": "## Create or update these exact files\n- `tests/test_task_queue.py`\n",
        "tasks/602.md": "## Create or update these exact files\n- `agents/run_task.py`\n",
    }

    result = be.execute_safe_lane_scheduler_mix_policy(
        queue=queue,
        task_text_loader=lambda task_path: task_texts[task_path],
        task_runner=lambda task_path, **_kwargs: {"entry": {"final_decision": "completed"}, "task_path": task_path},
        policy_artifact_path=(tmp_path / "scheduler_policy.json").as_posix(),
        now=lambda: "2026-04-09T21:10:00Z",
    )

    assert result["selection"]["selected_task_path"] == "tasks/601.md"
    assert result["autonomous_result"]["task_path"] == "tasks/601.md"
