from __future__ import annotations

from agents.lib import check_runner, git_ops, provider_client
from agents import run_task


def test_provider_client_dispatches_via_run_task_chat(monkeypatch):
    monkeypatch.setattr(provider_client, "chat_openai", lambda messages, model: "ok-openai")
    out = run_task.chat([{"role": "user", "content": "hi"}], model="gpt-5", provider="openai")
    assert out == "ok-openai"


def test_git_ops_helpers_preserve_branch_and_clean_checks(monkeypatch):
    calls = []

    def fake_capture(cmd):
        calls.append(("capture", tuple(cmd)))
        if cmd == ["git", "status", "--porcelain"]:
            return ""
        if cmd == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return "main"
        if cmd == ["git", "branch", "--list", "agent-x"]:
            return ""
        return ""

    def fake_run(cmd, check=True):
        calls.append(("run", tuple(cmd), check))
        class R:
            stdout = ""
        return R()

    monkeypatch.setattr(git_ops, "capture", fake_capture)
    monkeypatch.setattr(git_ops, "run", fake_run)

    run_task.ensure_clean_worktree()
    run_task.ensure_branch("agent-x")

    assert ("run", ("git", "checkout", "-b", "agent-x"), True) in calls


def test_check_runner_summary_shape_preserved(monkeypatch):
    class CP:
        def __init__(self, returncode: int, stdout: str):
            self.returncode = returncode
            self.stdout = stdout

    seq = [CP(0, "ruff ok"), CP(1, "1 failed")]

    def fake_capture_result(cmd):
        if cmd == ["ruff", "check", "."]:
            return seq[0]
        if cmd == ["pytest", "-q"]:
            return seq[1]
        raise AssertionError("unexpected command")

    monkeypatch.setattr(check_runner, "capture_result", fake_capture_result)
    result = check_runner.run_checks()

    assert result["lint_ok"] is True
    assert result["test_ok"] is False
    assert "pytest -q" in result["output_text"]


def test_run_task_public_surface_still_operates_with_extracted_modules(monkeypatch):
    monkeypatch.setattr(check_runner, "run_checks", lambda: {"lint_ok": True, "test_ok": True, "output_text": ""})
    ok, details = run_task.run_checks()
    assert ok
    assert details == ""
