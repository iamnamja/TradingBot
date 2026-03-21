from __future__ import annotations

from types import SimpleNamespace

import agents.run_task as run_task
from agents.lib import check_runner, git_ops, provider_client


def test_runtime_foundations_exports_present() -> None:
    exports = run_task._runtime_foundations_exports()
    assert exports["provider_client"] is provider_client
    assert exports["git_ops"] is git_ops
    assert exports["check_runner"] is check_runner


def test_provider_chat_dispatches_to_openai(monkeypatch) -> None:
    called = {"openai": 0}

    def fake_openai(messages, model):
        called["openai"] += 1
        assert messages == [{"role": "user", "content": "hi"}]
        assert model == "model-x"
        return "ok"

    monkeypatch.setattr(provider_client, "chat_openai", fake_openai)
    out = provider_client.chat([{"role": "user", "content": "hi"}], "model-x", provider="openai")
    assert out == "ok"
    assert called["openai"] == 1


def test_git_helpers_preserve_branch_and_cleanliness_behavior(monkeypatch) -> None:
    monkeypatch.setattr(git_ops, "capture", lambda cmd: "feature" if "rev-parse" in cmd else "")
    calls = []
    monkeypatch.setattr(git_ops, "run", lambda cmd, check=True: calls.append((cmd, check)))
    git_ops.ensure_branch("target")
    assert calls == [(["git", "checkout", "-B", "target"], True)]

    monkeypatch.setattr(git_ops, "capture", lambda cmd: " M file.py")
    try:
        git_ops.ensure_clean_worktree()
    except SystemExit as exc:
        assert "not clean" in str(exc)
    else:
        raise AssertionError("expected SystemExit")


def test_check_runner_summary_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        check_runner,
        "capture_result",
        lambda cmd: SimpleNamespace(returncode=1 if cmd[0] == "ruff" else 0, stdout="o", stderr="e"),
    )
    ok, details = check_runner.run_checks()
    assert ok is False
    assert "lint_ok" in details
    assert "test_ok" in details
    assert "output_text" in details


def test_run_task_public_surface_delegates(monkeypatch) -> None:
    monkeypatch.setattr(provider_client, "default_provider", lambda: "openai")
    monkeypatch.setattr(provider_client, "default_model_for_provider", lambda p: f"{p}-model")
    monkeypatch.setattr(provider_client, "chat_openai", lambda m, model: "openai-out")
    monkeypatch.setattr(provider_client, "chat_anthropic", lambda m, model: "anthropic-out")
    monkeypatch.setattr(provider_client, "chat", lambda m, model, provider=None: "chat-out")
    monkeypatch.setattr(git_ops, "run", lambda cmd, check=True: "ran")
    monkeypatch.setattr(git_ops, "capture", lambda cmd: "captured")
    monkeypatch.setattr(git_ops, "ensure_clean_worktree", lambda: None)
    monkeypatch.setattr(git_ops, "ensure_branch", lambda branch: None)
    monkeypatch.setattr(check_runner, "capture_result", lambda cmd: "result")
    monkeypatch.setattr(check_runner, "run_checks", lambda: (True, ""))

    assert run_task.default_provider() == "openai"
    assert run_task.default_model_for_provider("openai") == "openai-model"
    assert run_task.chat_openai([], "m") == "openai-out"
    assert run_task.chat_anthropic([], "m") == "anthropic-out"
    assert run_task.chat([], "m", provider="openai") == "chat-out"
    assert run_task.run(["git"]) == "ran"
    assert run_task.capture(["git"]) == "captured"
    assert run_task.capture_result(["pytest"]) == "result"
    run_task.ensure_clean_worktree()
    run_task.ensure_branch("b")
    assert run_task.run_checks() == (True, "")
