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
        return {"task_path": item.task_path, "attempt": attempts[item.task_path]}

    def validator(_item, _result):
        return True, "ok"

    def acceptance(item, result, _ok, _note):
        if item.task_path.endswith("001.md") and result["attempt"] == 1:
            return {"acceptance_decision": "retryable_failure", "note": "fix lint and retry"}
        return {"acceptance_decision": "accepted", "note": "accepted"}

    def retry(item, result, retry_count):
        repaired.append(f"{item.task_path}:{retry_count}")
        return {"task_path": item.task_path, "attempt": result["attempt"] + 1}

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
    assert outcomes[0]["retry_count"] == 1
    assert outcomes[0]["next_task_may_proceed"] is True
    assert outcomes[1]["acceptance_decision"] == "accepted"
    assert persisted[-1]["batch_status"] == "completed"


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
    assert persisted[-1]["checkpoints"][-1]["accepted_task_pr_flow_completed"] is False
    assert persisted[-1]["checkpoints"][-1]["clean_main_reset_completed"] is False


def test_resume_after_merge_does_not_skip_without_full_merge_reset_truth(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)
    state = bs.apply_task_result(
        state,
        task_path="tasks/001.md",
        terminal_status="completed",
        post_task_decision="continue",
        note="accepted but reset missing",
        acceptance_decision="accepted",
        next_task_may_proceed=True,
        accepted_task_pr_flow_completed=False,
        required_checks_passed=True,
        merged_to_main=True,
        clean_main_reset_completed=False,
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
    assert executed == ["tasks/001.md", "tasks/002.md"]
    assert [o["task_path"] for o in outcomes] == ["tasks/001.md", "tasks/002.md"]


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


def test_resume_after_manual_resolution_requires_explicit_operator_intent(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)
    state = bs.apply_task_result(
        state,
        task_path="tasks/001.md",
        terminal_status="manual_patch",
        post_task_decision="manual_patch",
        note="needs manual work",
        acceptance_decision="manual_patch",
        next_task_may_proceed=False,
    )

    persisted: list[dict[str, object]] = []

    def execute_task(_item):
        raise AssertionError("should not execute without explicit resume")

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
        resume_mode="resume_after_manual_resolution",
        explicit_resume=False,
        persist_state=lambda s: persisted.append(s.to_dict()),
    )

    assert final_decision == "manual_patch"
    assert outcomes == []
    assert resumed_state.resume_reason == "resume_after_manual_resolution"
    assert resumed_state.resume_target_task_path == "tasks/001.md"
    assert resumed_state.resume_gate == ""
    assert persisted[-1]["resume_target_task_path"] == "tasks/001.md"



def test_explicit_resume_after_manual_resolution_replays_target_task(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)
    state = bs.apply_task_result(
        state,
        task_path="tasks/001.md",
        terminal_status="manual_patch",
        post_task_decision="manual_patch",
        note="needs manual work",
        acceptance_decision="manual_patch",
        next_task_may_proceed=False,
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
        resume_mode="resume_after_manual_resolution",
        explicit_resume=True,
        persist_state=lambda _s: None,
    )

    assert final_decision == "continue"
    assert resumed_state.batch_status == "completed"
    assert executed == ["tasks/001.md", "tasks/002.md"]
    assert [o["task_path"] for o in outcomes] == ["tasks/001.md", "tasks/002.md"]


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
    assert result["accepted_task_pr_flow_completed"] is False
    assert result["merged_to_main"] is False
    assert result["clean_main_reset_completed"] is False


def test_hardened_short_manifest_proof_completes_after_non_reexecuting_self_heal(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    _write_task(tmp_path / "tasks" / "003.md")
    manifest = {"tasks": ["tasks/001.md", "tasks/002.md", "tasks/003.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)

    execution_attempts: dict[str, int] = {}
    repaired: list[str] = []

    def execute_task(item):
        execution_attempts[item.task_path] = execution_attempts.get(item.task_path, 0) + 1
        return {"task_path": item.task_path, "execution_attempt": execution_attempts[item.task_path], "repaired": False}

    def validator(_item, _result):
        return True, "ok"

    def acceptance(item, result, _ok, _note):
        if item.task_path.endswith("001.md") and not result.get("repaired"):
            return {"acceptance_decision": "retryable_failure", "note": "repair controller drift"}
        return {"acceptance_decision": "accepted", "note": "accepted"}

    def retry(item, result, retry_count):
        repaired.append(f"{item.task_path}:{retry_count}")
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

    assert final_decision == "continue"
    assert final_state.batch_status == "completed"
    assert execution_attempts == {
        "tasks/001.md": 1,
        "tasks/002.md": 1,
        "tasks/003.md": 1,
    }
    assert repaired == ["tasks/001.md:1"]
    assert [outcome["task_path"] for outcome in outcomes] == ["tasks/001.md", "tasks/002.md", "tasks/003.md"]
    assert outcomes[0]["acceptance_decision"] == "accepted"
    assert outcomes[0]["retry_count"] == 1
    assert outcomes[0]["next_task_may_proceed"] is True
    assert all(outcome["post_task_decision"] == "continue" for outcome in outcomes)


def test_hardened_short_manifest_proof_stops_on_failed_merge_then_resumes_honestly(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    be = _batch_executor_module()

    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")
    _write_task(tmp_path / "tasks" / "003.md")
    manifest = {"tasks": ["tasks/001.md", "tasks/002.md", "tasks/003.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)

    executed: list[str] = []
    persisted: list[dict[str, object]] = []

    def execute_task(item):
        executed.append(item.task_path)
        return {"task_path": item.task_path}

    def validator(_item, _result):
        return True, "ok"

    def acceptance(item, _result, _ok, _note):
        if item.task_path.endswith("001.md"):
            return {
                "acceptance_decision": "accepted",
                "note": "accepted and merged",
                "post_task_decision": "continue",
                "next_task_may_proceed": True,
                "accepted_task_pr_flow_completed": True,
                "required_checks_passed": True,
                "merged_to_main": True,
                "clean_main_reset_completed": True,
            }
        if item.task_path.endswith("002.md"):
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

    stopped_state, outcomes, final_decision = be.execute_batch_loop(
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
    assert stopped_state.batch_status == "failed_merge"
    assert executed == ["tasks/001.md", "tasks/002.md"]
    assert [outcome["task_path"] for outcome in outcomes] == ["tasks/001.md", "tasks/002.md"]
    assert persisted[-1]["checkpoints"][0]["clean_main_reset_completed"] is True
    assert persisted[-1]["checkpoints"][1]["clean_main_reset_completed"] is False

    resumed_state, resumed_outcomes, resumed_decision = be.execute_batch_loop(
        initial_state=stopped_state,
        queue=queue,
        execute_task=execute_task,
        run_authoritative_validation=validator,
        run_final_acceptance_review=lambda item, _result, _ok, _note: {
            "acceptance_decision": "accepted",
            "note": "accepted after operator retry",
            "post_task_decision": "continue",
            "next_task_may_proceed": True,
            "accepted_task_pr_flow_completed": True,
            "required_checks_passed": True,
            "merged_to_main": True,
            "clean_main_reset_completed": True,
        },
        self_heal_and_retry=retry,
        retry_budget=1,
        resume_mode="resume_after_merge",
        persist_state=lambda _s: None,
    )

    assert resumed_decision == "continue"
    assert resumed_state.batch_status == "completed"
    assert executed == ["tasks/001.md", "tasks/002.md", "tasks/002.md", "tasks/003.md"]
    assert [outcome["task_path"] for outcome in resumed_outcomes] == ["tasks/002.md", "tasks/003.md"]


def test_multi_agent_loop_role_trace_and_controller_authority_are_canonical() -> None:
    loop = _multi_agent_loop_module()

    def builder_step(_role_state):
        return {"changed_files": ["agents/run_task.py"], "summary": "builder patch ready"}

    def verifier_step(_builder_artifact, _role_state):
        return {
            "validator_ok": True,
            "validator_note": "validation passed",
            "focused_results": ["tests/test_run_task_runtime_foundations.py"],
            "full_results": ["pytest -q"],
            "acceptance_report": {
                "acceptance_decision": "accepted",
                "post_task_decision": "continue",
                "next_task_may_proceed": True,
                "note": "accepted",
            },
        }

    loop_result = loop.execute_multi_agent_loop(
        task_path="tasks/091_orchestrator_builder_verifier_controller_loop.md",
        builder_step=builder_step,
        verifier_step=verifier_step,
    )

    assert loop_result["role_trace"] == ["controller", "builder", "controller", "verifier", "controller"]
    assert loop_result["builder_artifact"]["artifact_kind"] == "builder_patch_attempt"
    assert loop_result["verifier_artifact"]["artifact_kind"] == "verifier_evidence_bundle"
    assert loop_result["controller_decision"]["final_authority_role"] == "controller"
    assert loop_result["controller_decision"]["action"] == "advance"


def test_dependency_aware_manifest_identifies_ready_vs_blocked_tasks(tmp_path: Path) -> None:
    tq = _task_queue_module()

    _write_task(tmp_path / 'tasks' / '001.md')
    _write_task(tmp_path / 'tasks' / '002.md')
    _write_task(tmp_path / 'tasks' / '003.md')
    manifest = {
        'tasks': [
            {'path': 'tasks/001.md', 'depends_on': ['tasks/002.md'], 'deferrable': True},
            'tasks/002.md',
            {'path': 'tasks/003.md', 'skipped_by_policy': True},
        ]
    }
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    truth = tq.plan_manifest_progress(queue)

    assert truth['ready_task_paths'] == ['tasks/002.md']
    assert truth['blocked_task_paths'] == ['tasks/001.md']
    assert truth['deferred_task_paths'] == ['tasks/001.md']
    assert truth['skipped_task_paths'] == ['tasks/003.md']
    assert truth['selected_task_path'] == 'tasks/002.md'
    assert truth['reordered'] is True
    assert truth['blocking_reasons']['tasks/001.md'].startswith('missing_prerequisites:')



def test_non_deferrable_blocker_prevents_reordering(tmp_path: Path) -> None:
    tq = _task_queue_module()

    _write_task(tmp_path / 'tasks' / '001.md')
    _write_task(tmp_path / 'tasks' / '002.md')
    manifest = {
        'tasks': [
            {'path': 'tasks/001.md', 'depends_on': ['tasks/002.md']},
            'tasks/002.md',
        ]
    }
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    truth = tq.plan_manifest_progress(queue)

    assert truth['blocked_task_paths'] == ['tasks/001.md']
    assert truth['selected_task_path'] == ''
    assert truth['reordered'] is False



def test_completed_prerequisite_unblocks_deferred_task_without_corrupting_queue_truth(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()

    _write_task(tmp_path / 'tasks' / '001.md')
    _write_task(tmp_path / 'tasks' / '002.md')
    manifest = {
        'tasks': [
            {'path': 'tasks/001.md', 'depends_on': ['tasks/002.md'], 'deferrable': True},
            'tasks/002.md',
        ]
    }
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source='tasks/manifest.json', created_ts=1)

    assert state.planner_selected_task_path == 'tasks/002.md'
    assert state.planner_blocked_task_paths == ('tasks/001.md',)

    state = bs.apply_task_result(
        state,
        task_path='tasks/002.md',
        terminal_status='completed',
        post_task_decision='continue',
        note='done',
        next_task_may_proceed=True,
    )

    assert state.planner_selected_task_path == 'tasks/001.md'
    assert state.planner_blocked_task_paths == ()
    assert state.queue[0].task_path == 'tasks/001.md'
    assert state.queue[1].status == 'completed'



def test_resume_reconstructs_dependency_planner_truth_deterministically(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()

    _write_task(tmp_path / 'tasks' / '001.md')
    _write_task(tmp_path / 'tasks' / '002.md')
    manifest = {
        'tasks': [
            {'path': 'tasks/001.md', 'depends_on': ['tasks/002.md'], 'deferrable': True},
            'tasks/002.md',
        ]
    }
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source='tasks/manifest.json', created_ts=1)
    state = bs.apply_task_result(
        state,
        task_path='tasks/002.md',
        terminal_status='completed',
        post_task_decision='continue',
        note='done',
        next_task_may_proceed=True,
    )

    resumed = bs.mark_resume_plan(
        state,
        queue=queue,
        resume_mode='resume_after_merge',
        resume_target_task_path='tasks/001.md',
        explicit_resume=False,
        updated_ts=2,
    )

    assert resumed.planner_selected_task_path == state.planner_selected_task_path
    assert resumed.planner_ready_task_paths == state.planner_ready_task_paths
    assert resumed.planner_blocking_reasons == state.planner_blocking_reasons


def test_planner_routing_and_verification_truth_stay_consistent_together(tmp_path: Path) -> None:
    tq = _task_queue_module()
    mal = _multi_agent_loop_module()

    _write_task(tmp_path / "tasks" / "001_foundation.md")
    _write_task(tmp_path / "tasks" / "002_followup.md")
    manifest = {
        "tasks": [
            {"path": "tasks/001_foundation.md"},
            {"path": "tasks/002_followup.md", "depends_on": ["tasks/001_foundation.md"]},
        ]
    }

    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    assert [item.task_path for item in queue] == ["tasks/001_foundation.md", "tasks/002_followup.md"]

    calls: list[tuple[str, str]] = []

    current_task_path = {"value": ""}

    def builder_step(role_state: dict[str, object]) -> dict[str, object]:
        calls.append((current_task_path["value"], "build"))
        return {"changed_files": [current_task_path["value"].replace(".md", ".py")], "summary": "built"}

    def verifier_step(_builder_artifact: dict[str, object], role_state: dict[str, object]) -> dict[str, object]:
        calls.append((current_task_path["value"], "verify"))
        return {
            "validator_ok": True,
            "validator_note": "local validation passed",
            "acceptance_report": {
                "acceptance_decision": "accepted",
                "post_task_decision": "continue",
                "next_task_may_proceed": True,
                "note": "accepted",
            },
        }

    def controller_decide(verifier_artifact: dict[str, object], _builder_artifact: dict[str, object], role_state: dict[str, object]) -> dict[str, object]:
        calls.append((current_task_path["value"], "decide"))
        return {
            "task_path": current_task_path["value"],
            "post_task_decision": "continue" if verifier_artifact["verdict"] == "pass" else "stop",
            "next_task_may_proceed": verifier_artifact["verdict"] == "pass",
            "summary": "verification accepted",
            "action": "advance" if verifier_artifact["verdict"] == "pass" else "stop",
        }

    decisions = []
    for item in queue:
        current_task_path["value"] = item.task_path
        result = mal.execute_multi_agent_loop(
            task_path=item.task_path,
            builder_step=builder_step,
            verifier_step=verifier_step,
            controller_decide=controller_decide,
        )
        decisions.append(result["controller_decision"]["post_task_decision"])

    assert decisions == ["continue", "continue"]
    assert calls == [
        ("tasks/001_foundation.md", "build"),
        ("tasks/001_foundation.md", "verify"),
        ("tasks/001_foundation.md", "decide"),
        ("tasks/002_followup.md", "build"),
        ("tasks/002_followup.md", "verify"),
        ("tasks/002_followup.md", "decide"),
    ]



def test_multi_agent_loop_supervised_mixed_manifest_stays_bounded() -> None:
    loop = _multi_agent_loop_module()
    result = loop.execute_multi_agent_loop(
        task_manifest={
            "tasks": [
                {"task_path": "tasks/089_orchestrator_hardened_autonomous_short_manifest_proof.md", "task_family": "proof_docs"},
                {"task_path": "tasks/106_orchestrator_external_workspace_bootstrap_recovery_proof.md", "task_family": "bootstrap"},
                {"task_path": "tasks/107_orchestrator_supervised_mixed_manifest_autonomy_reproof.md", "task_family": "consumer_facing"},
            ]
        },
        choose_next_role=lambda ctx: "builder" if ctx.get("phase") == "build" else ("verifier" if ctx.get("phase") == "verify" else "controller"),
        run_role=lambda role, ctx: (
            {"status": "built", "task_path": str(ctx["task_path"])} if role == "builder" else
            ({"accepted": True, "verification_authority": "local_only", "task_path": str(ctx["task_path"])} if role == "verifier" else
             {"controller_final_decision": "continue", "post_task_decision": "continue"})
        ),
    )

    assert result["processed_task_ids"] == [
        "089_orchestrator_hardened_autonomous_short_manifest_proof",
        "106_orchestrator_external_workspace_bootstrap_recovery_proof",
        "107_orchestrator_supervised_mixed_manifest_autonomy_reproof",
    ]
    assert result["runtime_portability_scope"] == "python_only"


def test_bounded_decomposition_required_for_large_mixed_ordinary_task_shape() -> None:
    mp = _manifest_planner_module()

    truth = mp.build_bounded_decomposition_truth([
        "agents/lib/agent_router.py",
        "agents/lib/task_contracts.py",
        "agents/lib/manifest_planner.py",
        "tests/test_task_queue.py",
        "docs/ORCHESTRATOR_PRODUCT_SPEC.md",
    ])

    assert truth["bounded_decomposition_required"] is True
    assert truth["decomposition_status"] == "required"
    assert truth["decomposition_unit_count"] >= 2
    assert any(unit["label"].startswith("code") for unit in truth["decomposition_units"])


def test_task_admission_context_marks_protected_meta_shape_manual_only() -> None:
    contracts = importlib.import_module("agents.lib.task_contracts")

    context = contracts.task_admission_context(
        ["agents/run_task.py", "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"],
        task_file="tasks/111_orchestrator_task_admission_and_decomposition_gate.md",
    )

    assert context["task_admission_lane"] == "manual_only"
    assert context["protected_or_meta_task"] is True
    assert context["bounded_decomposition_required"] is False


def test_task_family_context_keeps_small_verifier_only_shape_autonomous() -> None:
    contracts = importlib.import_module("agents.lib.task_contracts")

    context = contracts.task_family_task_context(
        ["tests/test_task_queue.py", "tests/test_run_task_runtime_foundations.py"],
        task_file="tasks/111_orchestrator_task_admission_and_decomposition_gate.md",
    )

    assert context["task_family"] == "verifier_first"
    assert context["task_admission_lane"] == "autonomous_ordinary"
    assert context["bounded_decomposition_required"] is False


def test_multi_agent_loop_marks_ordinary_execution_surface_for_autonomous_task() -> None:
    loop = _multi_agent_loop_module()

    result = loop.execute_multi_agent_loop(
        task_path="tasks/113_orchestrator_multi_role_ordinary_task_execution_loop.md",
        required_paths=["agents/lib/multi_agent_loop.py", "tests/test_task_queue.py"],
        builder_step=lambda role_state: {"changed_files": ["agents/lib/multi_agent_loop.py"], "summary": "updated ordinary loop"},
        verifier_step=lambda builder_artifact, role_state: {
            "validator_ok": True,
            "validator_note": "local validation passed",
            "focused_results": ["pytest -q tests/test_task_queue.py"],
            "full_results": ["pytest -q"],
            "acceptance_report": {
                "acceptance_decision": "accepted",
                "post_task_decision": "continue",
                "next_task_may_proceed": True,
                "note": "accepted",
            },
        },
    )

    assert result["task_context"]["task_admission_lane"] == "autonomous_ordinary"
    assert result["verifier_artifact"]["tester_execution_plan"]["validation_mode"] == "focused_then_broad"
    assert result["controller_decision"]["ordinary_task_execution_surface"] == "multi_role_ordinary_task"


def test_cross_task_repo_memory_persists_accepted_changes_and_unresolved_blockers(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()

    _write_task(tmp_path / "tasks" / "001_foundation.md")
    _write_task(tmp_path / "tasks" / "002_followup.md")
    _write_task(tmp_path / "tasks" / "003_optional.md")
    manifest = {
        "tasks": [
            {"path": "tasks/001_foundation.md"},
            {"path": "tasks/002_followup.md", "depends_on": ["tasks/001_foundation.md"]},
            {"path": "tasks/003_optional.md", "depends_on": ["tasks/002_followup.md"], "deferrable": True},
        ]
    }

    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = bs.initialize_batch_state(manifest=manifest, queue=queue, manifest_source="tasks/manifest.json", created_ts=1)
    state = bs.apply_task_result(
        state,
        task_path="tasks/001_foundation.md",
        terminal_status="completed",
        post_task_decision="continue",
        note="accepted foundation",
        acceptance_decision="accepted",
        next_task_may_proceed=True,
        coder_artifact_envelope={
            "summary": "Builder landed the foundation seam.",
            "changed_files": ["agents/lib/batch_state.py", "agents/run_task.py"],
        },
    )

    state = bs.apply_task_result(
        state,
        task_path="tasks/002_followup.md",
        terminal_status="blocked",
        post_task_decision="manual_patch",
        note="blocked on verifier follow-up",
        acceptance_decision="manual_patch",
        next_task_may_proceed=False,
        controller_artifact_envelope={"summary": "Controller deferred the remaining follow-up."},
    )

    carry = bs.carry_forward_context_for_task(state, task_path="tasks/003_optional.md")

    assert state.accepted_change_summaries[0]["task_path"] == "tasks/001_foundation.md"
    assert state.unresolved_blockers[0]["task_path"] == "tasks/002_followup.md"
    assert state.deferred_issue_summaries[0]["task_path"] == "tasks/003_optional.md"
    assert any(entry["memory_kind"] == "accepted_change" for entry in state.repo_memory_entries)
    assert any(entry["memory_kind"] == "unresolved_blocker" for entry in state.repo_memory_entries)
    assert carry["task_path"] == "tasks/003_optional.md"
    assert "Carry forward 1 accepted change(s), 1 unresolved blocker(s), and 1 deferred issue(s)." == carry["carry_forward_summary"]


def test_checkpoint_snapshots_repo_memory_deterministically(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()

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
        acceptance_decision="accepted",
        next_task_may_proceed=True,
        coder_artifact_envelope={"summary": "Builder changed one file.", "changed_files": ["agents/lib/check_runner.py"]},
    )

    checkpoint = bs.last_checkpoint_for_task(state, "tasks/001.md")
    assert checkpoint is not None
    assert checkpoint.accepted_change_summaries[0]["changed_files"] == ["agents/lib/check_runner.py"]
    assert checkpoint.carry_forward_summary == state.carry_forward_summary
