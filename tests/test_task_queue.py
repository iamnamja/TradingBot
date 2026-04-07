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


def _project_registry_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return importlib.import_module("agents.lib.project_registry")


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
    assert final_state.batch_status == "blocked"
    assert final_decision == "manual_patch"
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


def test_batch_state_is_project_scoped_and_carryforward_does_not_leak(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    pr = _project_registry_module()

    _write_task(tmp_path / "tasks" / "001.md")
    manifest = {"tasks": ["tasks/001.md"]}

    trading_contract = pr.resolve_project_contract("tradingbot_monorepo")
    external_contract = pr.resolve_project_contract("generic_python_external")

    trading_queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path, project_id=trading_contract["project_id"])
    external_queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path, project_id=external_contract["project_id"])

    trading_state = bs.initialize_batch_state(
        manifest=manifest,
        queue=trading_queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
        project_contract=trading_contract,
    )
    external_state = bs.initialize_batch_state(
        manifest=manifest,
        queue=external_queue,
        manifest_source="tasks/manifest.json",
        created_ts=2,
        project_contract=external_contract,
    )

    trading_context = bs.carry_forward_context_for_task(trading_state, task_path="tasks/001.md")
    external_context = bs.carry_forward_context_for_task(external_state, task_path="tasks/001.md")

    assert trading_context["project_id"] == "tradingbot_monorepo"
    assert external_context["project_id"] == "generic_python_external"
    assert trading_context["project_state_namespace"] != external_context["project_state_namespace"]
    assert trading_context["project_checkpoint_namespace"] != external_context["project_checkpoint_namespace"]
    assert trading_context["carry_forward_project_safe"] is True
    assert external_context["carry_forward_project_safe"] is True


def test_queue_signature_is_project_scoped(tmp_path: Path) -> None:
    tq = _task_queue_module()

    _write_task(tmp_path / "tasks" / "001.md")
    manifest = {"tasks": ["tasks/001.md"]}

    queue_a = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path, project_id="alpha")
    queue_b = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path, project_id="beta")

    assert tq.queue_signature(queue_a) == ("alpha:tasks/001.md",)
    assert tq.queue_signature(queue_b) == ("beta:tasks/001.md",)


def test_backlog_selector_prefers_highest_priority_ready_task(tmp_path: Path) -> None:
    tq = _task_queue_module()
    pr = _project_registry_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    _write_task(tmp_path / "tasks" / "003.md")

    manifest = {
        "tasks": [
            {"path": "tasks/001.md", "priority": 1},
            {"path": "tasks/002.md", "priority": 5},
            {"path": "tasks/003.md", "priority": 3, "depends_on": ["tasks/001.md"]},
        ]
    }
    contract = pr.resolve_project_contract("tradingbot_monorepo")
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path, project_id=contract["project_id"])

    truth = tq.select_next_backlog_task(queue, project_contract=contract)

    assert truth["selected_task_path"] == "tasks/002.md"
    assert truth["selected_reason"] == "selected_by_priority"
    assert truth["ranked_candidate_paths"][:2] == ["tasks/002.md", "tasks/001.md"]
    assert truth["blocking_reasons"]["tasks/003.md"] == "missing_prerequisites:tasks/001.md"


def test_backlog_selector_blocks_unsatisfied_authority_and_uses_carry_forward_memory(tmp_path: Path) -> None:
    tq = _task_queue_module()
    pr = _project_registry_module()

    _write_task(tmp_path / "tasks" / "010.md")
    _write_task(tmp_path / "tasks" / "011.md")
    _write_task(tmp_path / "tasks" / "012.md")

    manifest = {
        "tasks": [
            {"path": "tasks/010.md", "priority": 10, "authority_prerequisite": "hosted"},
            {"path": "tasks/011.md", "priority": 4},
            {"path": "tasks/012.md", "priority": 8},
        ]
    }
    contract = pr.resolve_project_contract("tradingbot_monorepo")
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path, project_id=contract["project_id"])
    repo_memory = {
        "carry_forward_summary": "Carry forward 0 accepted change(s), 1 unresolved blocker(s), and 0 deferred issue(s).",
        "unresolved_blockers": [{"task_path": "tasks/012.md", "summary": "Blocked previously"}],
    }

    truth = tq.select_next_backlog_task(queue, project_contract=contract, repo_memory=repo_memory, hosted_authority_ready=False)

    assert truth["selected_task_path"] == "tasks/011.md"
    assert truth["blocking_reasons"]["tasks/010.md"] == "authority_prerequisite_unsatisfied:hosted"
    assert truth["blocking_reasons"]["tasks/012.md"] == "carry_forward_blocked"
    assert truth["carry_forward_summary_used"].startswith("Carry forward")


def test_manifest_entry_schema_includes_priority_and_authority_prerequisite() -> None:
    planner = _manifest_planner_module()

    entry = planner.normalize_manifest_entry_schema({
        "path": "tasks/020.md",
        "priority": 7,
        "authority_prerequisite": "required_ci",
    })

    assert entry["priority"] == 7
    assert entry["authority_prerequisite"] == "hosted"
