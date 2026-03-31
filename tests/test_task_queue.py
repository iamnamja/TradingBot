from __future__ import annotations

from pathlib import Path

import pytest

from agents.lib.task_queue import (
    TaskQueueManifestError,
    TaskQueueTransitionError,
    build_task_queue_from_manifest,
    may_proceed_to_next_task,
    queue_signature,
    validate_queue_status_transition,
)


def _write_task(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# task\n", encoding="utf-8")


def test_valid_manifest_becomes_deterministic_queue(tmp_path: Path) -> None:
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

    queue = build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    assert [item.task_path for item in queue] == ["tasks/001.md", "tasks/002.md"]
    assert [item.ordinal for item in queue] == [1, 2]
    assert [item.status for item in queue] == ["queued", "queued"]
    assert queue[0].label == "alpha"
    assert queue[0].note == "first"
    assert queue[0].status_note == ""
    assert queue[0].stop_policy == "continue_on_failure"


def test_missing_task_files_are_surfaced_clearly(tmp_path: Path) -> None:
    manifest = {
        "tasks": ["tasks/missing-one.md", "tasks/missing-two.md"],
        "policy": {"duplicate_policy": "reject"},
    }

    with pytest.raises(TaskQueueManifestError) as exc:
        build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    msg = str(exc.value)
    assert "Missing task file(s):" in msg
    assert "tasks/missing-one.md" in msg
    assert "tasks/missing-two.md" in msg


def test_duplicate_task_paths_rejected_by_default_rule(tmp_path: Path) -> None:
    _write_task(tmp_path / "tasks" / "001.md")

    manifest = {
        "tasks": ["tasks/001.md", "tasks/001.md"],
        "policy": {"duplicate_policy": "reject"},
    }

    with pytest.raises(TaskQueueManifestError) as exc:
        build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    assert "Duplicate task path `tasks/001.md`" in str(exc.value)


def test_duplicate_task_paths_can_be_normalized_keep_first(tmp_path: Path) -> None:
    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")

    manifest = {
        "tasks": ["tasks/001.md", "tasks/001.md", "tasks/002.md", "tasks/002.md"],
        "policy": {"duplicate_policy": "dedupe_keep_first"},
    }

    queue = build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    assert [item.task_path for item in queue] == ["tasks/001.md", "tasks/002.md"]
    assert [item.ordinal for item in queue] == [1, 2]
    assert [item.status for item in queue] == ["queued", "queued"]


def test_queue_status_defaults_are_stable(tmp_path: Path) -> None:
    _write_task(tmp_path / "tasks" / "001.md")
    manifest = {"tasks": ["tasks/001.md"]}

    queue = build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    item = queue[0]
    assert item.status == "queued"
    assert item.status_note == ""


def test_queue_status_transitions_are_deterministic_and_narrow() -> None:
    validate_queue_status_transition("queued", "running")
    validate_queue_status_transition("running", "completed")
    validate_queue_status_transition("running", "failed")
    validate_queue_status_transition("running", "manual_patch")
    validate_queue_status_transition("running", "blocked")

    with pytest.raises(TaskQueueTransitionError):
        validate_queue_status_transition("queued", "completed")


def test_queue_signature_is_stable_for_resume_identity(tmp_path: Path) -> None:
    _write_task(tmp_path / "tasks" / "001.md")
    _write_task(tmp_path / "tasks" / "002.md")

    manifest = {"tasks": ["tasks/001.md", "tasks/002.md"]}
    queue = build_task_queue_from_manifest(manifest, repo_root=tmp_path)

    assert queue_signature(queue) == ("tasks/001.md", "tasks/002.md")


def test_may_proceed_to_next_task_only_when_completed() -> None:
    assert may_proceed_to_next_task("completed") is True
    assert may_proceed_to_next_task("failed") is False
    assert may_proceed_to_next_task("manual_patch") is False
    assert may_proceed_to_next_task("blocked") is False
    assert may_proceed_to_next_task("running") is False
    assert may_proceed_to_next_task("queued") is False
