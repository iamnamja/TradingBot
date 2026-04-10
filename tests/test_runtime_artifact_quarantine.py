from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_runtime_artifact_modules():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    run_task = importlib.import_module("agents.run_task")
    artifact_quarantine = importlib.import_module("agents.lib.artifact_quarantine")
    return run_task, artifact_quarantine


def test_classify_runtime_artifacts_known_safe_and_unknown() -> None:
    _, artifact_quarantine = _load_runtime_artifact_modules()
    classify_runtime_artifacts = artifact_quarantine.classify_runtime_artifacts

    paths = [
        Path("last_output.txt"),
        Path("_last_agent_model_output.txt"),
        Path("custom_runtime_dump.log"),
    ]

    classified = classify_runtime_artifacts(paths)

    assert [p.as_posix() for p in classified["known_safe"]] == [
        "last_output.txt",
        "_last_agent_model_output.txt",
    ]
    assert [p.as_posix() for p in classified["unknown"]] == ["custom_runtime_dump.log"]


def test_cleanup_runtime_artifacts_delegates_to_helper(monkeypatch) -> None:
    run_task, artifact_quarantine = _load_runtime_artifact_modules()
    known_safe_names = artifact_quarantine.KNOWN_SAFE_ARTIFACT_NAMES

    called = {"ok": False}
    seen: dict[str, object] = {}

    def fake_quarantine(
        paths,
        run_git_command,
        path_exists,
        unlink_path,
        known_safe_names=known_safe_names,
        retain_known_safe: bool = False,
    ):
        called["ok"] = True
        seen["paths"] = [p.as_posix() for p in paths]
        seen["known_safe_names"] = tuple(known_safe_names)
        seen["retain_known_safe"] = retain_known_safe
        _ = run_git_command
        _ = path_exists
        _ = unlink_path
        return {"classified": {"known_safe": list(paths), "unknown": []}, "should_block": False}

    monkeypatch.setattr(
        run_task,
        "_artifact_quarantine_exports",
        lambda: {
            "quarantine_runtime_artifacts": fake_quarantine,
            "known_safe_artifact_names": known_safe_names,
        },
    )

    run_task._cleanup_runtime_artifacts_for_commit([Path("last_output.txt")])

    assert called["ok"] is True
    assert seen["paths"] == ["last_output.txt"]
    assert seen["known_safe_names"] == known_safe_names
    assert seen["retain_known_safe"] is False


def test_quarantine_preserves_warning_audit_visibility() -> None:
    _, artifact_quarantine = _load_runtime_artifact_modules()
    quarantine_runtime_artifacts = artifact_quarantine.quarantine_runtime_artifacts

    git_calls: list[list[str]] = []
    removed: list[str] = []

    def fake_run_git(cmd, check=True):
        _ = check
        git_calls.append(list(cmd))
        return object()

    def fake_exists(_path: Path) -> bool:
        return True

    def fake_unlink(path: Path) -> None:
        removed.append(path.as_posix())

    result = quarantine_runtime_artifacts(
        [Path("last_output.txt"), Path("notes.tmp")],
        run_git_command=fake_run_git,
        path_exists=fake_exists,
        unlink_path=fake_unlink,
    )

    assert result["should_block"] is True
    assert result["warnings"]["quarantined_known_safe"] == ["last_output.txt"]
    assert result["warnings"]["unknown_artifacts"] == ["notes.tmp"]
    assert removed == ["last_output.txt"]
    assert any(cmd[:3] == ["git", "rm", "--cached"] for cmd in git_calls)
    assert any("last_output.txt" in cmd for cmd in git_calls)


def test_unknown_artifacts_still_block() -> None:
    _, artifact_quarantine = _load_runtime_artifact_modules()
    quarantine_runtime_artifacts = artifact_quarantine.quarantine_runtime_artifacts

    result = quarantine_runtime_artifacts(
        [Path("unexpected.bin")],
        run_git_command=lambda *args, **kwargs: object(),
        path_exists=lambda _p: False,
        unlink_path=lambda _p: None,
    )
    assert result["classified"]["known_safe"] == []
    assert [p.as_posix() for p in result["classified"]["unknown"]] == ["unexpected.bin"]
    assert result["should_block"] is True


def test_quarantined_artifacts_still_present_in_decision_output() -> None:
    _, artifact_quarantine = _load_runtime_artifact_modules()
    quarantine_runtime_artifacts = artifact_quarantine.quarantine_runtime_artifacts

    result = quarantine_runtime_artifacts(
        [Path("_last_agent_file_bundle.txt")],
        run_git_command=lambda *args, **kwargs: object(),
        path_exists=lambda _p: False,
        unlink_path=lambda _p: None,
    )
    assert result["classified"]["known_safe"][0].as_posix() == "_last_agent_file_bundle.txt"
    assert result["warnings"]["quarantined_known_safe"] == ["_last_agent_file_bundle.txt"]


def test_quarantine_unknown_only_does_not_require_git_cleanup() -> None:
    _, artifact_quarantine = _load_runtime_artifact_modules()
    quarantine_runtime_artifacts = artifact_quarantine.quarantine_runtime_artifacts

    git_calls: list[list[str]] = []

    def fake_run_git(cmd, check=True):
        _ = check
        git_calls.append(list(cmd))
        return object()

    result = quarantine_runtime_artifacts(
        [Path("scratch/random.out")],
        run_git_command=fake_run_git,
        path_exists=lambda _p: True,
        unlink_path=lambda _p: None,
    )

    assert result["warnings"]["quarantined_known_safe"] == []
    assert result["warnings"]["unknown_artifacts"] == ["scratch/random.out"]
    assert result["should_block"] is True
    assert git_calls == []



def test_bundle_error_artifact_is_known_safe() -> None:
    _, artifact_quarantine = _load_runtime_artifact_modules()
    classify_runtime_artifacts = artifact_quarantine.classify_runtime_artifacts

    classified = classify_runtime_artifacts([Path("_last_agent_file_bundle_error.txt")])

    assert [p.as_posix() for p in classified["known_safe"]] == ["_last_agent_file_bundle_error.txt"]
    assert classified["unknown"] == []
