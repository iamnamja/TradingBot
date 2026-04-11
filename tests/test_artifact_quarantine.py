from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_artifact_quarantine_module():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return importlib.import_module("agents.lib.artifact_quarantine")


def test_known_safe_runtime_artifacts_removed_on_default_push_path() -> None:
    artifact_quarantine = _load_artifact_quarantine_module()
    removed: list[str] = []
    git_calls: list[list[str]] = []

    result = artifact_quarantine.quarantine_runtime_artifacts(
        [Path("_last_agent_model_output.txt"), Path("_last_agent_file_bundle.txt")],
        run_git_command=lambda cmd, check=False: git_calls.append(cmd),
        path_exists=lambda _p: True,
        unlink_path=lambda p: removed.append(p.as_posix()),
    )

    assert result["should_block"] is False
    assert sorted(removed) == ["_last_agent_file_bundle.txt", "_last_agent_model_output.txt"]
    assert result["warnings"]["quarantined_known_safe"] == [
        "_last_agent_model_output.txt",
        "_last_agent_file_bundle.txt",
    ]
    assert result["warnings"]["retained_known_safe"] == []
    assert result["lifecycle"]["known_safe_action"] == "quarantined_removed"
    assert all(call[:3] == ["git", "rm", "--cached"] for call in git_calls)


def test_known_safe_runtime_artifacts_retained_when_explicit_control_enabled() -> None:
    artifact_quarantine = _load_artifact_quarantine_module()
    removed: list[str] = []
    git_calls: list[list[str]] = []

    result = artifact_quarantine.quarantine_runtime_artifacts(
        [Path("_last_agent_model_output.txt"), Path("_last_agent_file_bundle.txt")],
        run_git_command=lambda cmd, check=False: git_calls.append(cmd),
        path_exists=lambda _p: True,
        unlink_path=lambda p: removed.append(p.as_posix()),
        retain_known_safe=True,
    )

    assert result["should_block"] is False
    assert removed == []
    assert result["warnings"]["quarantined_known_safe"] == [
        "_last_agent_model_output.txt",
        "_last_agent_file_bundle.txt",
    ]
    assert result["warnings"]["retained_known_safe"] == [
        "_last_agent_model_output.txt",
        "_last_agent_file_bundle.txt",
    ]
    assert result["lifecycle"]["known_safe_action"] == "retained"
    assert len(git_calls) == 2


def test_retained_runtime_artifacts_are_unstaged_even_when_kept() -> None:
    artifact_quarantine = _load_artifact_quarantine_module()
    observed: list[list[str]] = []

    artifact_quarantine.quarantine_runtime_artifacts(
        [Path("_last_agent_model_output.txt")],
        run_git_command=lambda cmd, check=False: observed.append(cmd),
        path_exists=lambda _p: True,
        unlink_path=lambda _p: None,
        retain_known_safe=True,
    )

    assert observed == [["git", "rm", "--cached", "--quiet", "--ignore-unmatch", "_last_agent_model_output.txt"]]


def test_unknown_runtime_artifacts_still_block() -> None:
    artifact_quarantine = _load_artifact_quarantine_module()
    result = artifact_quarantine.quarantine_runtime_artifacts(
        [Path("mystery_runtime.tmp")],
        run_git_command=lambda *args, **kwargs: object(),
        path_exists=lambda _p: False,
        unlink_path=lambda _p: None,
    )

    assert result["classified"]["known_safe"] == []
    assert [p.as_posix() for p in result["classified"]["unknown"]] == ["mystery_runtime.tmp"]
    assert result["warnings"]["unknown_artifacts"] == ["mystery_runtime.tmp"]
    assert result["should_block"] is True


def test_classify_runtime_artifacts_with_known_safe_defaults() -> None:
    artifact_quarantine = _load_artifact_quarantine_module()
    classified = artifact_quarantine.classify_runtime_artifacts(
        [Path(name) for name in artifact_quarantine.KNOWN_SAFE_ARTIFACT_NAMES] + [Path("unknown.dat")]
    )
    assert [p.name for p in classified["known_safe"]] == list(artifact_quarantine.KNOWN_SAFE_ARTIFACT_NAMES)
    assert [p.name for p in classified["unknown"]] == ["unknown.dat"]


def test_describe_runtime_artifact_lifecycle_for_retained_and_blocked_states() -> None:
    artifact_quarantine = _load_artifact_quarantine_module()
    retained = artifact_quarantine.describe_runtime_artifact_lifecycle({
        "warnings": {
            "quarantined_known_safe": ["_last_agent_model_output.txt"],
            "retained_known_safe": ["_last_agent_model_output.txt"],
            "unknown_artifacts": [],
        },
        "lifecycle": {"known_safe_action": "retained", "unknown_action": "none"},
    })
    blocked = artifact_quarantine.describe_runtime_artifact_lifecycle({
        "warnings": {
            "quarantined_known_safe": [],
            "retained_known_safe": [],
            "unknown_artifacts": ["mystery_runtime.tmp"],
        },
        "lifecycle": {"known_safe_action": "quarantined_removed", "unknown_action": "blocked"},
    })

    assert "Retained known-safe runtime artifacts" in retained[0]
    assert "Unknown runtime artifacts remain blocked" in blocked[0]


def test_classify_runtime_artifacts_includes_subset_preservation_artifact() -> None:
    artifact_quarantine = _load_artifact_quarantine_module()
    classified = artifact_quarantine.classify_runtime_artifacts(
        [Path("_last_subset_preservation.json")]
    )

    assert [p.name for p in classified["known_safe"]] == ["_last_subset_preservation.json"]
    assert classified["unknown"] == []
