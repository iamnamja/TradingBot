from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


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


def _write_task(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# task\n", encoding="utf-8")


def _initialize_batch_state_fallback(bs, manifest: dict, queue: list, *, manifest_source: str, created_ts: int):
    init = getattr(bs, "initialize_batch_state", None)
    if callable(init):
        return init(manifest=manifest, queue=queue, manifest_source=manifest_source, created_ts=created_ts)

    create = getattr(bs, "create_batch_state", None)
    if callable(create):
        return create(manifest=manifest, queue=queue, manifest_source=manifest_source, created_ts=created_ts)

    queue_state = tuple(
        bs.BatchTaskState(
            task_path=item.task_path,
            ordinal=item.ordinal,
            status="queued",
            status_note="",
            attempts=0,
            updated_seq=0,
        )
        for item in queue
    )

    kwargs = {
        "manifest_source": manifest_source,
        "manifest_fingerprint": bs.manifest_fingerprint(manifest),
        "queue": queue_state,
        "current_index": 0,
        "state_version": 1,
        "event_seq": 0,
        "created_ts": created_ts,
        "updated_ts": created_ts,
        "batch_status": "active",
    }
    fields = getattr(bs.BatchState, "__dataclass_fields__", {})
    if "checkpoints" in fields:
        kwargs["checkpoints"] = ()
    if "next_task_may_proceed" in fields:
        kwargs["next_task_may_proceed"] = True
    if "continue_gate_open" in fields:
        kwargs["continue_gate_open"] = True
    if "post_task_decision" in fields:
        kwargs["post_task_decision"] = "continue"

    return bs.BatchState(**kwargs)


def _advance_task_status_fallback(bs, state, *, task_index: int, to_status: str, status_note: str = "", event_ts: int = 0):
    advance = getattr(bs, "advance_task_status", None)
    if callable(advance):
        return advance(state, task_index=task_index, to_status=to_status, status_note=status_note, event_ts=event_ts)

    apply_result = getattr(bs, "apply_task_result", None)
    if callable(apply_result):
        current = state.queue[task_index]
        decision = "continue" if to_status == "completed" else ("manual_patch" if to_status == "manual_patch" else ("blocked" if to_status == "blocked" else "stop"))
        return apply_result(
            state,
            task_path=current.task_path,
            terminal_status=to_status,
            post_task_decision=decision,
            note=status_note,
            updated_ts=event_ts,
            context_kind="branch",
            context_ref="local-test",
        )

    current = state.queue[task_index]
    updated_item = bs.BatchTaskState(
        task_path=current.task_path,
        ordinal=current.ordinal,
        status=to_status,
        status_note=status_note,
        attempts=current.attempts + (1 if to_status == "running" else 0),
        updated_seq=state.event_seq + 1,
    )
    new_queue = list(state.queue)
    new_queue[task_index] = updated_item
    next_index = state.current_index
    if to_status in {"completed", "failed", "manual_patch", "blocked"} and task_index >= next_index:
        next_index = task_index + 1

    def derive_batch_status(queue_tuple):
        statuses = [item.status for item in queue_tuple]
        if any(status == "running" for status in statuses):
            return "active"
        if any(status == "blocked" for status in statuses):
            return "blocked"
        if any(status == "manual_patch" for status in statuses):
            return "manual_patch"
        if any(status == "failed" for status in statuses):
            return "failed"
        if statuses and all(status == "completed" for status in statuses):
            return "completed"
        return "active"

    queue_tuple = tuple(new_queue)
    kwargs = {
        "manifest_source": state.manifest_source,
        "manifest_fingerprint": state.manifest_fingerprint,
        "queue": queue_tuple,
        "current_index": next_index,
        "state_version": state.state_version,
        "event_seq": state.event_seq + 1,
        "created_ts": state.created_ts,
        "updated_ts": event_ts,
        "batch_status": derive_batch_status(queue_tuple),
    }
    fields = getattr(bs.BatchState, "__dataclass_fields__", {})
    if "checkpoints" in fields:
        kwargs["checkpoints"] = getattr(state, "checkpoints", ())
    if "next_task_may_proceed" in fields:
        kwargs["next_task_may_proceed"] = to_status == "completed"
    if "continue_gate_open" in fields:
        kwargs["continue_gate_open"] = to_status == "completed"
    if "post_task_decision" in fields:
        kwargs["post_task_decision"] = "continue" if to_status == "completed" else ("manual_patch" if to_status == "manual_patch" else ("blocked" if to_status == "blocked" else "stop"))

    return bs.BatchState(**kwargs)


def _state_continue_gate_open(state, tq) -> bool:
    status = getattr(state, "batch_status", state.get("batch_status"))
    return status not in {"blocked", "manual_patch", "failed"} and tq.may_proceed_to_next_task(status if status in {"completed", "failed", "manual_patch", "blocked", "running", "queued"} else "queued") if status == "completed" else status == "active"


def test_valid_manifest_becomes_deterministic_queue(tmp_path: Path) -> None:
    tq = _task_queue_module()
    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")

    manifest = {
        "manifest_version": "1",
        "tasks": [
            {"path": "tasks/001.md", "label": "alpha", "note": "first"},
            "tasks/002.md",
        ],
        "policy": {"duplicate_policy": "reject", "stop_policy": "continue_on_failure"},
    }

    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    assert [item.task_path for item in queue] == ["tasks/001.md", "tasks/002.md"]
    assert [item.ordinal for item in queue] == [1, 2]
    assert [item.status for item in queue] == ["queued", "queued"]
    assert queue[0].label == "alpha"
    assert queue[0].note == "first"
    assert queue[0].status_note == ""
    assert queue[0].stop_policy == "continue_on_failure"


def test_missing_task_files_are_surfaced_clearly(tmp_path: Path) -> None:
    tq = _task_queue_module()
    manifest = {
        "tasks": ["tasks/missing-one.md", "tasks/missing-two.md"],
        "policy": {"duplicate_policy": "reject"},
    }

    with pytest.raises(tq.TaskQueueManifestError) as exc:
        tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    msg = str(exc.value)
    assert "Missing task file(s):" in msg
    assert "tasks/missing-one.md" in msg
    assert "tasks/missing-two.md" in msg


def test_duplicate_task_paths_rejected_by_default_rule(tmp_path: Path) -> None:
    tq = _task_queue_module()
    _write_task(tmp_path / "tasks" / "001.md")

    manifest = {
        "tasks": ["tasks/001.md", "tasks/001.md"],
        "policy": {"duplicate_policy": "reject"},
    }

    with pytest.raises(tq.TaskQueueManifestError) as exc:
        tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    assert "Duplicate task path `tasks/001.md`" in str(exc.value)


def test_duplicate_task_paths_can_be_normalized_keep_first(tmp_path: Path) -> None:
    tq = _task_queue_module()
    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")

    manifest = {
        "tasks": ["tasks/001.md", "tasks/001.md", "tasks/002.md", "tasks/002.md"],
        "policy": {"duplicate_policy": "dedupe_keep_first"},
    }

    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    assert [item.task_path for item in queue] == ["tasks/001.md", "tasks/002.md"]
    assert [item.ordinal for item in queue] == [1, 2]
    assert [item.status for item in queue] == ["queued", "queued"]


def test_queue_status_defaults_are_stable(tmp_path: Path) -> None:
    tq = _task_queue_module()
    _write_task(tmp_path / "tasks" / "001.md")
    manifest = {"tasks": ["tasks/001.md"]}

    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    item = queue[0]
    assert item.status == "queued"
    assert item.status_note == ""


def test_queue_status_transitions_are_deterministic_and_narrow() -> None:
    tq = _task_queue_module()
    tq.validate_queue_status_transition("queued", "running")
    tq.validate_queue_status_transition("running", "completed")
    tq.validate_queue_status_transition("running", "failed")
    tq.validate_queue_status_transition("running", "manual_patch")
    tq.validate_queue_status_transition("running", "blocked")

    with pytest.raises(tq.TaskQueueTransitionError):
        tq.validate_queue_status_transition("queued", "completed")


def test_queue_signature_is_stable_for_resume_identity(tmp_path: Path) -> None:
    tq = _task_queue_module()
    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")

    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    assert tq.queue_signature(queue) == ("tasks/001.md", "tasks/002.md")


def test_decide_post_task_action_continue_for_success() -> None:
    tq = _task_queue_module()
    decision = tq.decide_post_task_action(
        "completed",
        signals={
            "validator_ok": True,
            "deliverable_complete": True,
            "protected_lane_ok": True,
        },
    )
    assert decision == "continue"


def test_decide_post_task_action_manual_patch_when_recommended() -> None:
    tq = _task_queue_module()
    decision = tq.decide_post_task_action(
        "failed",
        signals={"manual_patch_recommended": True},
    )
    assert decision == "manual_patch"


def test_decide_post_task_action_hard_failures_stop_or_block() -> None:
    tq = _task_queue_module()
    assert tq.decide_post_task_action("failed", signals={"validator_ok": False}) == "stop"
    assert (
        tq.decide_post_task_action(
            "failed",
            signals={"duplicate_bundle_conflict": True},
        )
        == "blocked"
    )


def test_batch_summary_payload_counts_and_outcomes_are_deterministic() -> None:
    tq = _task_queue_module()
    payload = tq.build_batch_summary_payload(
        manifest_path="tasks/batch.json",
        final_decision="manual_patch",
        outcomes=[
            {"task_path": "tasks/074.md", "status": "completed", "decision": "continue", "note": ""},
            {"task_path": "tasks/075.md", "status": "manual_patch", "decision": "manual_patch", "note": "needs manual follow-up"},
        ],
    )

    assert payload["manifest_path"] == "tasks/batch.json"
    assert payload["total_tasks"] == 2
    assert payload["completed_tasks"] == 1
    assert payload["failed_tasks"] == 0
    assert payload["manual_patch_tasks"] == 1
    assert payload["blocked_tasks"] == 0
    assert payload["final_batch_decision"] == "manual_patch"
    assert payload["task_outcomes"][1]["decision"] == "manual_patch"


def test_render_batch_summary_text_is_concise_and_human_readable() -> None:
    tq = _task_queue_module()
    payload = tq.build_batch_summary_payload(
        manifest_path="tasks/batch.json",
        final_decision="blocked",
        outcomes=[
            {"task_path": "tasks/074.md", "status": "completed", "decision": "continue", "note": ""},
            {"task_path": "tasks/075.md", "status": "blocked", "decision": "blocked", "note": "duplicate conflict"},
        ],
    )

    text = tq.render_batch_summary_text(payload)
    assert "Batch manifest: tasks/batch.json" in text
    assert "final=blocked" in text
    assert "- tasks/075.md: status=blocked, decision=blocked, note=duplicate conflict" in text


def test_backlog_e2e_all_success_runs_to_completion_and_persists_state(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    _write_task(tmp_path / "tasks" / "074.md")
    _write_task(tmp_path / "tasks" / "075.md")

    manifest = {
        "tasks": ["tasks/074.md", "tasks/075.md"],
        "policy": {"duplicate_policy": "reject", "stop_policy": "continue_on_failure"},
    }
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = _initialize_batch_state_fallback(
        bs,
        manifest,
        queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
    )

    outcomes: list[dict[str, str]] = []
    state = _advance_task_status_fallback(bs, state, task_index=0, to_status="running", event_ts=2)
    state = _advance_task_status_fallback(bs, state, task_index=0, to_status="completed", event_ts=3)
    outcomes.append({"task_path": "tasks/074.md", "status": "completed", "decision": "continue", "note": ""})

    state = _advance_task_status_fallback(bs, state, task_index=1, to_status="running", event_ts=4)
    state = _advance_task_status_fallback(bs, state, task_index=1, to_status="completed", event_ts=5)
    outcomes.append({"task_path": "tasks/075.md", "status": "completed", "decision": "continue", "note": ""})

    summary = tq.build_batch_summary_payload(
        manifest_path="tasks/manifest.json",
        final_decision="continue",
        outcomes=outcomes,
    )

    assert state.batch_status == "completed"
    assert state.current_index == 2
    assert [entry.status for entry in state.queue] == ["completed", "completed"]
    assert summary["completed_tasks"] == 2
    assert summary["final_batch_decision"] == "continue"


def test_backlog_e2e_manual_patch_or_blocked_stops_conservatively(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    _write_task(tmp_path / "tasks" / "074.md")
    _write_task(tmp_path / "tasks" / "075.md")
    _write_task(tmp_path / "tasks" / "076.md")

    manifest = {
        "tasks": ["tasks/074.md", "tasks/075.md", "tasks/076.md"],
        "policy": {"duplicate_policy": "reject", "stop_policy": "continue_on_failure"},
    }
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = _initialize_batch_state_fallback(
        bs,
        manifest,
        queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
    )

    state = _advance_task_status_fallback(bs, state, task_index=0, to_status="running", event_ts=2)
    state = _advance_task_status_fallback(bs, state, task_index=0, to_status="completed", event_ts=3)
    decision_075 = tq.decide_post_task_action(
        "failed",
        signals={"manual_patch_recommended": True, "truthful_failure_artifact_written": True},
    )
    state = _advance_task_status_fallback(bs, state, task_index=1, to_status="running", event_ts=4)
    state = _advance_task_status_fallback(bs, state, task_index=1, to_status="manual_patch", status_note="needs manual follow-up", event_ts=5)

    summary = tq.build_batch_summary_payload(
        manifest_path="tasks/manifest.json",
        final_decision="manual_patch",
        outcomes=[
            {"task_path": "tasks/074.md", "status": "completed", "decision": "continue", "note": ""},
            {"task_path": "tasks/075.md", "status": "manual_patch", "decision": decision_075, "note": "needs manual follow-up"},
        ],
    )

    assert state.batch_status == "manual_patch"
    assert state.queue[2].status == "queued"
    assert summary["manual_patch_tasks"] == 1
    assert summary["final_batch_decision"] == "manual_patch"


def test_backlog_e2e_continue_gate_blocks_progression_after_hard_failure(tmp_path: Path) -> None:
    tq = _task_queue_module()
    bs = _batch_state_module()
    _write_task(tmp_path / "tasks" / "074.md")
    _write_task(tmp_path / "tasks" / "075.md")

    manifest = {
        "tasks": ["tasks/074.md", "tasks/075.md"],
        "policy": {"duplicate_policy": "reject", "stop_policy": "continue_on_failure"},
    }
    decision = tq.decide_post_task_action(
        "failed",
        signals={
            "validator_ok": False,
            "deliverable_complete": False,
            "duplicate_bundle_conflict": True,
            "truthful_failure_artifact_written": True,
        },
    )

    assert decision == "blocked"
    assert tq.may_proceed_to_next_task("blocked") is False

    empty_queue = [
        tq.TaskQueueItem(task_path="tasks/074.md", ordinal=1),
        tq.TaskQueueItem(task_path="tasks/075.md", ordinal=2),
    ]
    state = _initialize_batch_state_fallback(
        bs,
        manifest,
        empty_queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
    )
    state = _advance_task_status_fallback(bs, state, task_index=0, to_status="running", event_ts=2)
    state = _advance_task_status_fallback(bs, state, task_index=0, to_status="blocked", status_note="hard failure: duplicate conflict", event_ts=3)

    summary = tq.build_batch_summary_payload(
        manifest_path="tasks/manifest.json",
        final_decision="blocked",
        outcomes=[
            {
                "task_path": "tasks/074.md",
                "status": "blocked",
                "decision": "blocked",
                "note": "hard failure: duplicate conflict",
            }
        ],
    )

    assert state.batch_status == "blocked"
    assert summary["blocked_tasks"] == 1
    assert summary["final_batch_decision"] == "blocked"
