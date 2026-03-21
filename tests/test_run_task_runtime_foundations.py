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
    return run_task, check_runner, git_ops, provider_client


def test_provider_client_delegation(monkeypatch) -> None:
    run_task, _, _, provider_client = _load_runtime_modules()

    def fake_chat(messages, model, provider=None):
        assert model == "m"
        assert provider == "openai"
        return "ok"

    monkeypatch.setattr(provider_client, "chat", fake_chat)
    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "ok"


def test_git_helpers_behavior(monkeypatch) -> None:
    run_task, _, git_ops, _ = _load_runtime_modules()
    calls: list[tuple[list[str], bool]] = []

    def fake_capture(cmd: list[str]) -> str:
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return ""
        if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return "main"
        raise AssertionError(cmd)

    def fake_run(cmd: list[str], check: bool = True):
        calls.append((cmd, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(git_ops, "capture", fake_capture)
    monkeypatch.setattr(git_ops, "run", fake_run)

    run_task.ensure_clean_worktree()
    run_task.ensure_branch("feature-x")

    assert (["git", "checkout", "-B", "feature-x"], True) in calls


def test_check_runner_summary(monkeypatch) -> None:
    run_task, check_runner, _, _ = _load_runtime_modules()
    lint = SimpleNamespace(returncode=0, stdout="lint out\n", stderr="")
    test = SimpleNamespace(returncode=1, stdout="test out\n", stderr="test err\n")
    seq = [lint, test]

    def fake_capture_result(cmd):
        return seq.pop(0)

    monkeypatch.setattr(check_runner, "capture_result", fake_capture_result)

    ok, text = run_task.run_checks()

    assert ok is False
    assert "=== ruff check . ===" in text
    assert "=== pytest -q ===" in text
    assert "lint out" in text
    assert "test out" in text
    assert "test err" in text
    assert "exit_code=0" in text
    assert "exit_code=1" in text


def test_public_surface_still_available() -> None:
    run_task, _, _, _ = _load_runtime_modules()
    assert callable(run_task.default_provider)
    assert callable(run_task.default_model_for_provider)
    assert callable(run_task.chat_openai)
    assert callable(run_task.chat_anthropic)
    assert callable(run_task.chat)
    assert callable(run_task.run)
    assert callable(run_task.capture)
    assert callable(run_task.capture_result)
    assert callable(run_task.ensure_clean_worktree)
    assert callable(run_task.ensure_branch)
    assert callable(run_task.run_checks)
