from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace


def _load_runtime_modules():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    run_task = importlib.import_module("agents.run_task")
    check_runner = importlib.import_module("agents.lib.check_runner")
    git_ops = importlib.import_module("agents.lib.git_ops")
    provider_client = importlib.import_module("agents.lib.provider_client")
    task_contracts = importlib.import_module("agents.lib.task_contracts")
    return run_task, check_runner, git_ops, provider_client, task_contracts


def test_provider_client_delegation(monkeypatch) -> None:
    run_task, _, _, provider_client, _ = _load_runtime_modules()

    def fake_chat(messages, model, provider=None):
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "ok"

    monkeypatch.setattr(provider_client, "chat", fake_chat)
    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "ok"


def test_git_helpers_behavior(monkeypatch) -> None:
    run_task, _, git_ops, _, _ = _load_runtime_modules()
    calls: list[tuple[list[str], bool]] = []

    def fake_capture(cmd: list[str]) -> str:
        if cmd == ["git", "status", "--porcelain"]:
            return ""
        if cmd == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return "main"
        if cmd == ["git", "branch", "--list", "feature-x"]:
            return ""
        raise AssertionError(cmd)

    def fake_run(cmd: list[str], check: bool = True):
        calls.append((cmd, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(git_ops, "capture", fake_capture)
    monkeypatch.setattr(git_ops, "run", fake_run)

    run_task.ensure_clean_worktree()
    run_task.ensure_branch("feature-x")

    assert any(cmd == ["git", "checkout", "-b", "feature-x"] for cmd, _ in calls) or any(
        cmd == ["git", "checkout", "-B", "feature-x"] for cmd, _ in calls
    )


def test_task_family_classifier_detects_integration_and_split() -> None:
    _, _, _, _, task_contracts = _load_runtime_modules()

    out = task_contracts.classify_task_family(
        task_text="Add integration coverage for protected-file method mode.",
        required_paths=["tests/test_integration_runner.py", "agents/lib/shell_router.py"],
    )

    assert out["integration_test"] is True
    assert out["protected_meta_harness"] is True
    assert out["split_recommended"] is True


def test_task_family_classifier_detects_docs_only_lane() -> None:
    _, _, _, _, task_contracts = _load_runtime_modules()

    out = task_contracts.classify_task_family(
        task_text="Refresh orchestrator docs.",
        required_paths=["docs/ORCHESTRATOR_VISION_AND_CONTROLS.md"],
    )

    assert out["docs_only"] is True
    assert out["integration_test"] is False


def test_lane_prompt_compiler_shapes_per_lane() -> None:
    _, _, _, _, task_contracts = _load_runtime_modules()

    docs_shape = task_contracts.compile_lane_prompt_shape(
        lane="docs-only",
        task_text="Update docs",
        required_paths=["docs/x.md"],
    )
    integ_shape = task_contracts.compile_lane_prompt_shape(
        lane="integration-test",
        task_text="Add integration coverage",
        required_paths=["tests/test_integration_runner.py"],
    )

    assert "docs-only" in docs_shape.lower()
    assert "integration-test" in integ_shape.lower()
    assert docs_shape != integ_shape
