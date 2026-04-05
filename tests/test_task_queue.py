from __future__ import annotations

import importlib
import json
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


def _new_state(bs, manifest: dict, queue, *, created_ts: int):
    fp = bs.manifest_fingerprint(manifest)
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
    return bs.BatchState(
        manifest_source="tasks/manifest.json",
        manifest_fingerprint=fp,
        queue=queue_state,
        checkpoints=(),
        current_index=0,
        state_version=2,
        event_seq=0,
        created_ts=created_ts,
        updated_ts=created_ts,
        batch_status="active",
        next_task_may_proceed=True,
        post_task_decision="continue",
    )


def _checkpoint_for(bs, state, *, task_path: str, status: str, decision: str, note: str, event_seq: int):
    index = next(i for i, item in enumerate(state.queue) if item.task_path == task_path)
    ordinal = state.queue[index].ordinal
    transitions = {
        "completed": "completed_clean",
        "manual_patch": "manual_patch_requires_isolation",
        "blocked": "blocked_requires_manual",
        "failed": "failed_requires_cleanup",
    }
    return bs.BatchTaskCheckpoint(
        task_path=task_path,
        ordinal=ordinal,
        context_kind="branch",
        context_ref=f"agent-{ordinal}",
        completed_cleanly=status == "completed",
        cleanup_required_before_next_task=decision != "continue",
        next_task_may_proceed=decision == "continue",
        transition=transitions[status],
        note=note,
        event_seq=event_seq,
        post_task_decision=decision,
    )


def _apply_terminal(bs, state, *, task_path: str, status: str, decision: str, note: str, updated_ts: int):
    event_seq = state.event_seq + 1
    queue_list = list(state.queue)
    index = next(i for i, item in enumerate(queue_list) if item.task_path == task_path)
    current = queue_list[index]
    queue_list[index] = bs.BatchTaskState(
        task_path=current.task_path,
        ordinal=current.ordinal,
        status=status,
        status_note=note,
        attempts=current.attempts + 1,
        updated_seq=event_seq,
    )
    checkpoint = _checkpoint_for(
        bs,
        state,
        task_path=task_path,
        status=status,
        decision=decision,
        note=note,
        event_seq=event_seq,
    )
    if status == "manual_patch":
        batch_status = "manual_patch"
    elif status == "blocked":
        batch_status = "blocked"
    elif status == "failed":
        batch_status = "failed"
    elif all(item.status == "completed" for item in queue_list):
        batch_status = "completed"
    else:
        batch_status = "active"
    return bs.BatchState(
        manifest_source=state.manifest_source,
        manifest_fingerprint=state.manifest_fingerprint,
        queue=tuple(queue_list),
        checkpoints=state.checkpoints + (checkpoint,),
        current_index=index + 1,
        state_version=state.state_version,
        event_seq=event_seq,
        created_ts=state.created_ts,
        updated_ts=updated_ts,
        batch_status=batch_status,
        next_task_may_proceed=decision == "continue",
        post_task_decision=decision,
    )


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
            {"task_path": "tasks/075.md", "status": "manual_patch", "note": "needs manual follow-up"},
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
    state = _new_state(bs, manifest, queue, created_ts=1)

    outcomes: list[dict[str, str]] = []
    for index, item in enumerate(queue, start=1):
        decision = tq.decide_post_task_action(
            "completed",
            signals={
                "validator_ok": True,
                "deliverable_complete": True,
                "protected_lane_ok": True,
            },
        )
        state = _apply_terminal(
            bs,
            state,
            task_path=item.task_path,
            status="completed",
            decision=decision,
            note="",
            updated_ts=index + 1,
        )
        outcomes.append({"task_path": item.task_path, "status": "completed", "decision": decision, "note": ""})

    summary = tq.build_batch_summary_payload(
        manifest_path="tasks/manifest.json",
        final_decision="continue",
        outcomes=outcomes,
    )
    serialized = json.loads(json.dumps(state.to_dict()))

    assert state.batch_status == "completed"
    assert state.next_task_may_proceed is True
    assert state.current_index == 2
    assert [entry["status"] for entry in serialized["queue"]] == ["completed", "completed"]
    assert serialized["manifest"]["source"] == "tasks/manifest.json"
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
    state = _new_state(bs, manifest, queue, created_ts=1)

    outcomes: list[dict[str, str]] = []

    decision_074 = tq.decide_post_task_action(
        "completed",
        signals={"validator_ok": True, "deliverable_complete": True, "protected_lane_ok": True},
    )
    state = _apply_terminal(
        bs,
        state,
        task_path="tasks/074.md",
        status="completed",
        decision=decision_074,
        note="",
        updated_ts=2,
    )
    outcomes.append({"task_path": "tasks/074.md", "status": "completed", "decision": decision_074, "note": ""})

    decision_075 = tq.decide_post_task_action(
        "failed",
        signals={"manual_patch_recommended": True},
    )
    state = _apply_terminal(
        bs,
        state,
        task_path="tasks/075.md",
        status="manual_patch",
        decision=decision_075,
        note="needs manual follow-up",
        updated_ts=3,
    )
    outcomes.append(
        {
            "task_path": "tasks/075.md",
            "status": "manual_patch",
            "decision": decision_075,
            "note": "needs manual follow-up",
        }
    )

    summary = tq.build_batch_summary_payload(
        manifest_path="tasks/manifest.json",
        final_decision="manual_patch",
        outcomes=outcomes,
    )
    serialized = json.loads(json.dumps(state.to_dict()))

    assert state.batch_status == "manual_patch"
    assert state.next_task_may_proceed is False
    assert serialized["queue"][2]["status"] == "queued"
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
    queue = tq.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = _new_state(bs, manifest, queue, created_ts=1)

    decision = tq.decide_post_task_action(
        "failed",
        signals={
            "validator_ok": False,
            "deliverable_complete": False,
            "duplicate_bundle_conflict": True,
        },
    )
    state = _apply_terminal(
        bs,
        state,
        task_path="tasks/074.md",
        status="blocked",
        decision=decision,
        note="hard failure: duplicate conflict",
        updated_ts=2,
    )

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
    serialized = json.loads(json.dumps(state.to_dict()))

    assert state.next_task_may_proceed is False
    assert state.batch_status == "blocked"
    assert serialized["queue"][1]["status"] == "queued"
    assert summary["blocked_tasks"] == 1
    assert summary["final_batch_decision"] == "blocked"
