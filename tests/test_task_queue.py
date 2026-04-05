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


def _write_task(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# task\n", encoding="utf-8")


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
