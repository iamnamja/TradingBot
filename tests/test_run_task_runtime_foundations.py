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
    controller_contract = importlib.import_module("agents.lib.controller_contract")
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
        controller_contract,
        final_acceptance,
        batch_executor,
    )


def test_provider_client_delegation(monkeypatch) -> None:
    run_task, _, _, provider_client, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    def fake_chat(messages, model, provider=None):
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "ok"

    monkeypatch.setattr(provider_client, "chat", fake_chat)
    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "ok"


def test_git_helpers_behavior(monkeypatch) -> None:
    run_task, _, git_ops, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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
    run_task, check_runner, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

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
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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
    assert callable(run_task.build_final_acceptance_failure_feedback)
    assert callable(run_task.report_final_acceptance_failure)
    assert callable(run_task.execute_batch_loop)
    assert callable(run_task.accepted_task_pr_merge_flow)
    assert callable(run_task.report_branch_push_ready)


def test_run_task_runtime_contract_modules_share_canonical_surface() -> None:
    (_, _, _, _, failure_journal, _, _, _, _, batch_state, task_queue, controller_contract, _, batch_executor) = _load_runtime_modules()
    assert task_queue.BatchPostTaskDecision is controller_contract.BatchPostTaskDecision
    assert batch_state.BatchStatus is controller_contract.BatchStatus
    assert batch_executor.ResumeMode is controller_contract.ResumeMode
    assert failure_journal.POLICY_BLOCKED_FAILURE_CATEGORY == controller_contract.POLICY_BLOCKED_FAILURE_CATEGORY



def test_failure_classifier_distinguishes_multiple_categories() -> None:
    _, _, _, _, failure_journal, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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
        == "policy_blocked"
    )

def test_prepare_resumed_batch_state_requires_explicit_manual_resolution_resume(tmp_path: Path) -> None:
    (_, _, _, _, _, _, _, _, _, batch_state, task_queue, _, _, batch_executor) = _load_runtime_modules()

    task_path = tmp_path / "tasks" / "001.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text("# task\n", encoding="utf-8")
    manifest = {"tasks": ["tasks/001.md"]}
    queue = task_queue.build_task_queue_from_manifest(manifest, repo_root=tmp_path)
    state = batch_state.initialize_batch_state(
        manifest=manifest,
        queue=queue,
        manifest_source="tasks/manifest.json",
        created_ts=1,
    )
    state = batch_state.apply_task_result(
        state,
        task_path="tasks/001.md",
        terminal_status="manual_patch",
        post_task_decision="manual_patch",
        note="needs manual work",
        acceptance_decision="manual_patch",
        next_task_may_proceed=False,
    )

    resumed = batch_executor.prepare_resumed_batch_state(
        state=state,
        queue=queue,
        resume_mode="resume_after_manual_resolution",
        explicit_resume=False,
    )
    assert resumed.resume_reason == "resume_after_manual_resolution"
    assert resumed.resume_target_task_path == "tasks/001.md"
    assert resumed.resume_gate == ""

    explicit_resumed = batch_executor.prepare_resumed_batch_state(
        state=state,
        queue=queue,
        resume_mode="resume_after_manual_resolution",
        explicit_resume=True,
    )
    assert explicit_resumed.resume_gate == "resume_after_manual_resolution"
    assert explicit_resumed.current_index == 0


def test_git_workflow_success_reports_canonical_merge_reset_truth() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    git_workflow = importlib.import_module("agents.lib.git_workflow")

    calls: list[list[str]] = []

    def runner(cmd: list[str], check: bool = True):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = git_workflow.accepted_task_pr_merge_flow(
        runner,
        accepted=True,
        autonomous_merge_enabled=True,
        pr_title="x",
        pr_body="",
    )

    assert calls[:4] == [
        ["gh", "pr", "create", "--fill", "--title", "x", "--body", ""],
        ["gh", "pr", "checks", "--watch"],
        ["gh", "pr", "merge", "--merge", "--auto", "--delete-branch"],
        ["git", "switch", "main"],
    ]
    assert result["post_task_decision"] == "continue"
    assert result["accepted_task_pr_flow_completed"] is True
    assert result["required_checks_passed"] is True
    assert result["merged_to_main"] is True
    assert result["clean_main_reset_completed"] is True
    assert result["next_task_may_proceed"] is True
