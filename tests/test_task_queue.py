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

    assert final_decision == "manual_patch"
    assert final_state.batch_status == "manual_patch"
    assert len(outcomes) == 1
    assert outcomes[0]["acceptance_decision"] == "manual_patch"
    assert outcomes[0]["next_task_may_proceed"] is False


def test_retryable_self_heal_then_accept_and_continue(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(
        manifest=manifest,
        queue=queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
    )

    attempts: dict[str, int] = {}
    repaired: list[str] = []
    persisted: list[dict[str, object]] = []

    def execute_task(item):
        attempts[item.task_path] = attempts.get(item.task_path, 0) + 1
        return {
            "task_path": item.task_path,
            "execution_attempt": attempts[item.task_path],
            "repaired": False,
            "repair_count": 0,
        }

    def validator(_item, _result):
        return True, "ok"

    def acceptance(item, result, _ok, _note):
        if item.task_path.endswith("001.md") and not result.get("repaired", False):
            return {"acceptance_decision": "retryable_failure", "note": "fix lint and repair"}
        return {"acceptance_decision": "accepted", "note": "accepted"}

    def retry(item, result, retry_count):
        repaired.append(f"{item.task_path}:{retry_count}")
        return {
            **result,
            "repaired": True,
            "repair_count": retry_count,
        }

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
    assert attempts["tasks/001.md"] == 1
    assert attempts["tasks/002.md"] == 1
    assert repaired == ["tasks/001.md:1"]
    assert [o["task_path"] for o in outcomes] == ["tasks/001.md", "tasks/002.md"]
    assert outcomes[0]["acceptance_decision"] == "accepted"
    assert outcomes[0]["execution_attempt_count"] == 1
    assert outcomes[0]["repair_count"] == 1
    assert outcomes[0]["accepted_after_repair"] is True
    assert outcomes[0]["retry_count"] == 1
    assert outcomes[0]["next_task_may_proceed"] is True
    assert outcomes[1]["acceptance_decision"] == "accepted"
    assert outcomes[1]["execution_attempt_count"] == 1
    assert outcomes[1]["repair_count"] == 0
    assert outcomes[1]["accepted_after_repair"] is False
    assert final_state.checkpoints[0].execution_attempt_count == 1
    assert final_state.checkpoints[0].repair_count == 1
    assert final_state.checkpoints[0].accepted_after_repair is True
    assert persisted[-1]["batch_status"] == "completed"



def test_retryable_self_heal_stays_bounded_by_repair_budget(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    manifest = {"tasks": ["tasks/001.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(
        manifest=manifest,
        queue=queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
    )

    attempts: dict[str, int] = {}
    repairs: list[int] = []

    def execute_task(item):
        attempts[item.task_path] = attempts.get(item.task_path, 0) + 1
        return {"task_path": item.task_path, "repaired": False}

    def validator(_item, _result):
        return True, "ok"

    def acceptance(_item, _result, _ok, _note):
        return {"acceptance_decision": "retryable_failure", "note": "still retryable"}

    def retry(_item, result, retry_count):
        repairs.append(retry_count)
        return {**result, "repaired": True, "repair_count": retry_count}

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

    assert final_decision == "stop"
    assert final_state.batch_status == "failed"
    assert attempts["tasks/001.md"] == 1
    assert repairs == [1]
    assert outcomes[0]["execution_attempt_count"] == 1
    assert outcomes[0]["repair_count"] == 1
    assert outcomes[0]["accepted_after_repair"] is False
    assert outcomes[0]["acceptance_decision"] == "retryable_failure"


def test_conservative_stop_on_merge_posture_failure_and_persisted_truth(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(
        manifest=manifest,
        queue=queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
    )

    persisted: list[dict[str, object]] = []

    def execute_task(item):
        return {"task_path": item.task_path}

    def validator(_item, _result):
        return True, "ok"

    def acceptance(item, _result, _ok, _note):
        if item.task_path.endswith("001.md"):
            return {
                "acceptance_decision": "accepted",
                "note": "accepted but merge failed",
                "post_task_decision": "failed_merge",
                "next_task_may_proceed": False,
                "accepted_task_pr_flow_completed": False,
                "required_checks_passed": False,
                "merged_to_main": False,
                "clean_main_reset_completed": False,
            }
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

    assert final_decision == "failed_merge"
    assert final_state.batch_status == "failed_merge"
    assert len(outcomes) == 1
    assert outcomes[0]["task_path"] == "tasks/001.md"
    assert outcomes[0]["acceptance_decision"] == "accepted"
    assert outcomes[0]["post_task_decision"] == "failed_merge"
    assert outcomes[0]["next_task_may_proceed"] is False
    assert outcomes[0]["merged_to_main"] is False
    assert persisted[-1]["batch_status"] == "failed_merge"


def test_resume_skips_previously_accepted_and_merged_tasks(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    _write_task(tmp_path / "tasks" / "003.md")
    manifest = {"tasks": ["tasks/001.md", "tasks/002.md", "tasks/003.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)
    state = bs.apply_task_result(
        state,
        task_path="tasks/001.md",
        terminal_status="completed",
        post_task_decision="continue",
        note="accepted and merged",
        acceptance_decision="accepted",
        next_task_may_proceed=True,
        accepted_task_pr_flow_completed=True,
        required_checks_passed=True,
        merged_to_main=True,
        clean_main_reset_completed=True,
    )

    executed: list[str] = []

    def execute_task(item):
        executed.append(item.task_path)
        return {"task_path": item.task_path}

    def validator(_item, _result):
        return True, "ok"

    def acceptance(_item, _result, _ok, _note):
        return {"acceptance_decision": "accepted", "note": "accepted"}

    def retry(_item, result, _retry_count):
        return result

    resumed_state, outcomes, final_decision = be.execute_batch_loop(
        initial_state=state,
        queue=queue,
        execute_task=execute_task,
        run_authoritative_validation=validator,
        run_final_acceptance_review=acceptance,
        self_heal_and_retry=retry,
        retry_budget=1,
        resume_mode="resume_after_merge",
        persist_state=lambda _s: None,
    )

    assert final_decision == "continue"
    assert resumed_state.batch_status == "completed"
    assert executed == ["tasks/002.md", "tasks/003.md"]
    assert [o["task_path"] for o in outcomes] == ["tasks/002.md", "tasks/003.md"]

def test_task_queue_uses_canonical_post_task_decision_surface(tmp_path: Path) -> None:
    tq = _task_queue_module()
    contract = _controller_contract_module()

    assert tq.BatchPostTaskDecision is contract.BatchPostTaskDecision
    assert tq.decide_post_task_action("completed") == "continue"
    assert tq.decide_post_task_action("manual_patch") == "manual_patch"
    assert tq.decide_post_task_action("blocked") == "blocked"


def test_batch_state_persists_canonical_truth_fields(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    contract = _controller_contract_module()

    _write_task(tmp_path / "tasks" / "001.md")
    manifest = {"tasks": ["tasks/001.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)
    state = bs.apply_task_result(
        state,
        task_path="tasks/001.md",
        terminal_status="completed",
        post_task_decision="continue",
        note="accepted",
        updated_ts=2,
        acceptance_decision="accepted",
        execution_attempt_count=1,
        repair_count=1,
        accepted_after_repair=True,
        retry_count=1,
        next_task_may_proceed=True,
        accepted_task_pr_flow_completed=True,
        required_checks_passed=True,
        merged_to_main=True,
        clean_main_reset_completed=True,
    )

    checkpoint = state.checkpoints[-1].to_dict()
    for field_name in contract.CHECKPOINT_TRUTH_FIELDS:
        assert field_name in checkpoint
    state_payload = state.to_dict()
    for field_name in contract.RESUME_METADATA_FIELDS:
        assert field_name in state_payload


def test_git_workflow_reports_canonical_merge_posture_decision() -> None:
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    git_workflow = importlib.import_module("agents.lib.git_workflow")

    def failing_runner(_cmd, _check=True):
        raise RuntimeError("checks blew up")

    result = git_workflow.accepted_task_pr_merge_flow(
        failing_runner,
        accepted=True,
        autonomous_merge_enabled=True,
        pr_title="x",
        pr_body="",
    )
    assert result["post_task_decision"] == "failed_merge"
