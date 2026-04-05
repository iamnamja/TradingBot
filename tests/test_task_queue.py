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
        updated_ts=2,
        context_kind="branch",
        context_ref="test",
        acceptance_decision="accepted",
        retry_count=0,
        next_task_may_proceed=True,
    )

    executed: list[str] = []

    def execute(item):
        executed.append(item.task_path)
        return {"task_path": item.task_path}

    final_state, outcomes, final_decision = be.execute_batch_loop(
        initial_state=state,
        queue=queue,
        execute_task=execute,
        run_authoritative_validation=lambda _i, _r: (True, "ok"),
        run_final_acceptance_review=lambda _i, _r, _ok, _n: {"acceptance_decision": "accepted", "note": "accepted"},
        self_heal_and_retry=lambda _i, r, _c: r,
        retry_budget=0,
        persist_state=lambda _s: None,
        resume_mode="resume_after_merge",
        explicit_resume=True,
    )

    assert executed == ["tasks/002.md", "tasks/003.md"]
    assert len(outcomes) == 2
    assert final_decision == "continue"
    assert final_state.resume_gate == "continue_from_next_pending"


def test_manual_resolution_resume_requires_explicit_mode(tmp_path: Path) -> None:
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
        note="manual patch required",
        updated_ts=2,
        context_kind="branch",
        context_ref="test",
        acceptance_decision="manual_patch",
        retry_count=0,
        next_task_may_proceed=False,
    )

    blocked = False
    try:
        be.execute_batch_loop(
            initial_state=state,
            queue=queue,
            execute_task=lambda _item: {"ok": True},
            run_authoritative_validation=lambda _i, _r: (True, "ok"),
            run_final_acceptance_review=lambda _i, _r, _ok, _n: {"acceptance_decision": "accepted", "note": "accepted"},
            self_heal_and_retry=lambda _i, r, _c: r,
            retry_budget=0,
            persist_state=lambda _s: None,
            resume_mode="resume_after_manual_resolution",
            resume_target_task_path="tasks/001.md",
            explicit_resume=False,
        )
    except Exception:
        blocked = True

    assert blocked is True

    resumed_state, outcomes, _ = be.execute_batch_loop(
        initial_state=state,
        queue=queue,
        execute_task=lambda item: {"task_path": item.task_path},
        run_authoritative_validation=lambda _i, _r: (True, "ok"),
        run_final_acceptance_review=lambda _i, _r, _ok, _n: {"acceptance_decision": "accepted", "note": "accepted"},
        self_heal_and_retry=lambda _i, r, _c: r,
        retry_budget=0,
        persist_state=lambda _s: None,
        resume_mode="resume_after_manual_resolution",
        resume_target_task_path="tasks/001.md",
        explicit_resume=True,
    )
    assert resumed_state.resume_reason == "resume_after_manual_resolution"
    assert resumed_state.resume_target_task_path == "tasks/001.md"
    assert resumed_state.resume_gate == "explicit_manual_resolution"
    assert len(outcomes) >= 1


def test_resume_state_persists_reason_and_target(tmp_path: Path) -> None:
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
        note="accepted and merged",
        updated_ts=2,
        context_kind="branch",
        context_ref="test",
        acceptance_decision="accepted",
        retry_count=0,
        next_task_may_proceed=True,
    )

    persisted: list[dict[str, object]] = []
    final_state, _outcomes, _decision = be.execute_batch_loop(
        initial_state=state,
        queue=queue,
        execute_task=lambda item: {"task_path": item.task_path},
        run_authoritative_validation=lambda _i, _r: (True, "ok"),
        run_final_acceptance_review=lambda _i, _r, _ok, _n: {"acceptance_decision": "accepted", "note": "accepted"},
        self_heal_and_retry=lambda _i, r, _c: r,
        retry_budget=0,
        persist_state=lambda s: persisted.append(s.to_dict()),
        resume_mode="resume_after_merge",
        explicit_resume=True,
    )

    assert persisted
    first = persisted[0]
    assert first["resume_reason"] in {"skip_accepted_merged", "resume_next"}
    assert first["resume_gate"] == "continue_from_next_pending"
    assert isinstance(first["resume_target_task_path"], str)
    assert final_state.resume_gate == "continue_from_next_pending"
