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
    failure_journal = importlib.import_module("agents.lib.failure_journal")
    task_contracts = importlib.import_module("agents.lib.task_contracts")
    failure_artifacts = importlib.import_module("agents.lib.failure_artifacts")
    shell_router = importlib.import_module("agents.lib.shell_router")
    artifact_quarantine = importlib.import_module("agents.lib.artifact_quarantine")
    batch_state = importlib.import_module("agents.lib.batch_state")
    task_queue = importlib.import_module("agents.lib.task_queue")
    final_acceptance = importlib.import_module("agents.lib.final_acceptance")
    batch_executor = importlib.import_module("agents.lib.batch_executor")
    return (
        run_task,
        check_runner,
        git_ops,
        provider_client,
        failure_journal,
        task_contracts,
        failure_artifacts,
        shell_router,
        artifact_quarantine,
        batch_state,
        task_queue,
        final_acceptance,
        batch_executor,
    )


def test_provider_client_delegation(monkeypatch) -> None:
    run_task, _, _, provider_client, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    def fake_chat(messages, model, provider=None):
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "ok"

    monkeypatch.setattr(provider_client, "chat", fake_chat)
    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "ok"


def test_git_helpers_behavior(monkeypatch) -> None:
    run_task, _, git_ops, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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


def test_check_runner_summary(monkeypatch) -> None:
    run_task, check_runner, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    def fake_capture_result(cmd):
        if cmd == ["ruff", "check", "."]:
            return SimpleNamespace(returncode=0, stdout="lint out\n", stderr="")
        if cmd == ["pytest", "-q"]:
            return SimpleNamespace(returncode=1, stdout="test out\n", stderr="test err\n")
        raise AssertionError(cmd)

    monkeypatch.setattr(check_runner, "capture_result", fake_capture_result)
    ok, text = run_task.run_checks()
    assert ok is False
    assert "=== pytest -q ===" in text
    assert "test out" in text


def test_public_surface_still_available() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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
    assert callable(run_task.parse_required_files)
    assert callable(run_task.validate_exact_deliverable_contract)
    assert callable(run_task.keep_runtime_artifacts_requested)
    assert callable(run_task.build_final_acceptance_report)
    assert callable(run_task.classify_final_acceptance_failure)
    assert callable(run_task.build_acceptance_self_heal_context)


def test_failure_classifier_distinguishes_multiple_categories() -> None:
    _, _, _, _, failure_journal, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    assert (
        failure_journal.classify_failure("tests", "SyntaxError: invalid syntax in generated test")
        == "python_syntax"
    )
    assert (
        failure_journal.classify_failure(
            "bundle_transport", "references invented seam alias failure_journal_export"
        )
        == "seam_contract_mismatch"
    )
    assert (
        failure_journal.classify_failure(
            "policy", "Protected meta file(s) in normal bundle lane"
        )
        == "harness_meta_regression"
    )


def test_batch_executor_retry_and_stop_behaviors() -> None:
    _, _, _, _, _, _, _, _, _, bs, tq, _, be = _load_runtime_modules()

    queue = [
        tq.TaskQueueItem(task_path="tasks/001.md", ordinal=1),
        tq.TaskQueueItem(task_path="tasks/002.md", ordinal=2),
    ]
    state = bs.initialize_batch_state(
        manifest={"tasks": ["tasks/001.md", "tasks/002.md"]},
        queue=queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
    )

    calls = {"exec": 0, "retry": 0}

    def execute(item):
        calls["exec"] += 1
        return {"task_path": item.task_path, "attempt": calls["exec"]}

    def validator(_item, _result):
        return True, "ok"

    def acceptance(item, _result, _ok, _note):
        if item.task_path.endswith("001.md") and calls["retry"] == 0:
            return {"acceptance_decision": "retryable_failure", "note": "retry once"}
        if item.task_path.endswith("001.md"):
            return {"acceptance_decision": "accepted", "note": "accepted"}
        return {"acceptance_decision": "blocked", "note": "blocked by policy"}

    def retry(_item, result, _retry_count):
        calls["retry"] += 1
        return result

    final_state, outcomes, final_decision = be.execute_batch_loop(
        initial_state=state,
        queue=queue,
        execute_task=execute,
        run_authoritative_validation=validator,
        run_final_acceptance_review=acceptance,
        self_heal_and_retry=retry,
        retry_budget=1,
        persist_state=lambda _s: None,
    )

    assert calls["retry"] == 1
    assert len(outcomes) == 2
    assert outcomes[0]["terminal_status"] == "completed"
    assert outcomes[1]["terminal_status"] == "blocked"
    assert final_decision == "blocked"
    assert final_state.batch_status == "blocked"


def test_batch_executor_resume_state_gate_and_skip_semantics() -> None:
    _, _, _, _, _, _, _, _, _, bs, tq, _, be = _load_runtime_modules()

    queue = [
        tq.TaskQueueItem(task_path="tasks/001.md", ordinal=1),
        tq.TaskQueueItem(task_path="tasks/002.md", ordinal=2),
    ]
    state = bs.initialize_batch_state(
        manifest={"tasks": ["tasks/001.md", "tasks/002.md"]},
        queue=queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
    )
    state = bs.apply_task_result(
        state,
        task_path="tasks/001.md",
        terminal_status="completed",
        post_task_decision="continue",
        note="accepted and merged",
        updated_ts=2,
        context_kind="branch",
        context_ref="test",
        acceptance_decision="accepted",
        retry_count=0,
        next_task_may_proceed=True,
    )

    executed: list[str] = []

    def execute(item):
        executed.append(item.task_path)
        return {"task_path": item.task_path}

    final_state, outcomes, _ = be.execute_batch_loop(
        initial_state=state,
        queue=queue,
        execute_task=execute,
        run_authoritative_validation=lambda _i, _r: (True, "ok"),
        run_final_acceptance_review=lambda _i, _r, _ok, _n: {"acceptance_decision": "accepted", "note": "accepted"},
        self_heal_and_retry=lambda _i, r, _c: r,
        retry_budget=0,
        persist_state=lambda _s: None,
        resume_mode="resume_after_merge",
        explicit_resume=True,
    )

    assert executed == ["tasks/002.md"]
    assert len(outcomes) == 1
    assert final_state.resume_reason in {"skip_accepted_merged", "resume_next"}
    assert final_state.resume_gate == "continue_from_next_pending"
