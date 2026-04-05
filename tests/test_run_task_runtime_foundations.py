from __future__ import annotations

import importlib
import json
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
    )


def test_provider_client_delegation(monkeypatch) -> None:
    run_task, _, _, provider_client, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    def fake_chat(messages, model, provider=None):
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "ok"

    monkeypatch.setattr(provider_client, "chat", fake_chat)
    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "ok"


def test_git_helpers_behavior(monkeypatch) -> None:
    run_task, _, git_ops, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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
    run_task, check_runner, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

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
    run_task, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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


def test_failure_classifier_distinguishes_multiple_categories() -> None:
    _, _, _, _, failure_journal, _, _, _, _, _, _, _ = _load_runtime_modules()
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


def test_failure_remediation_plans_choose_different_paths() -> None:
    _, _, _, _, failure_journal, _, _, _, _, _, _, _ = _load_runtime_modules()
    syntax_plan = failure_journal.build_failure_remediation_plan(
        kind="tests",
        message="SyntaxError: invalid syntax",
        category="python_syntax",
        retry_count=1,
        fingerprint="python_syntax:abc123",
        raw_failure_snippet="SyntaxError",
    )
    harness_plan = failure_journal.build_failure_remediation_plan(
        kind="policy",
        message="Protected meta file(s) in normal bundle lane",
        category="harness_meta_regression",
        retry_count=1,
        fingerprint="harness_meta_regression:def456",
        raw_failure_snippet="Protected meta file(s)",
    )

    assert syntax_plan["recommended_next_action"] == "retry_with_targeted_fix"
    assert syntax_plan["chosen_remediation_path"] == "targeted_syntax_repair"
    assert syntax_plan["continue_autonomously"] is True

    assert harness_plan["recommended_next_action"] == "manual_patch"
    assert harness_plan["chosen_remediation_path"] == "manual_patch_lane"
    assert harness_plan["continue_autonomously"] is False
    assert harness_plan["manual_lane_recommended"] is True


def test_runtime_artifact_placeholder_contains_checkpoint_fields(tmp_path: Path) -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    last_output = tmp_path / "last_output.json"
    last_bundle = tmp_path / "last_bundle.json"

    run_task._emit_failure_artifact_messages(
        last_output,
        last_bundle,
        create_placeholders=True,
        task_file="tasks/072.md",
        failure_category="tests",
        before_model_output=True,
        reason="early failure",
    )

    payload = json.loads(last_output.read_text(encoding="utf-8"))
    checkpoint = payload["batch_checkpoint"]
    assert checkpoint["task_file"] == "tasks/072.md"
    assert checkpoint["cleanup_required_before_next_task"] is True
    assert checkpoint["next_task_may_proceed"] is False
    assert checkpoint["transition"] == "failed_before_model_output"


def test_post_task_policy_gates_next_task_after_manual_patch() -> None:
    _, _, _, _, _, _, _, _, _, _, task_queue, _ = _load_runtime_modules()

    decision = task_queue.decide_post_task_action(
        "failed",
        signals={
            "manual_patch_recommended": True,
            "validator_ok": True,
            "deliverable_complete": True,
        },
    )

    assert decision == "manual_patch"
    assert task_queue.may_proceed_to_next_task("manual_patch") is False


def test_final_acceptance_report_accepts_matching_required_paths() -> None:
    _, _, _, _, _, _, _, _, _, _, _, final_acceptance = _load_runtime_modules()
    report = final_acceptance.build_final_acceptance_report(
        task_file="tasks/076.md",
        validated_required_paths=["agents/lib/final_acceptance.py", "tests/test_run_task_runtime_foundations.py"],
        head_diff_paths=["agents/lib/final_acceptance.py", "tests/test_run_task_runtime_foundations.py"],
        working_tree_paths=[],
        validation_profile={"passed": True, "details": ""},
    )
    assert report["acceptance_decision"] == "accepted"
    assert report["issues"] == []


def test_final_acceptance_report_rejects_missing_required_in_head() -> None:
    _, _, _, _, _, _, _, _, _, _, _, final_acceptance = _load_runtime_modules()
    report = final_acceptance.build_final_acceptance_report(
        task_file="tasks/076.md",
        validated_required_paths=["agents/lib/final_acceptance.py", "tests/test_run_task_runtime_foundations.py"],
        head_diff_paths=["tests/test_run_task_runtime_foundations.py"],
        working_tree_paths=[],
        validation_profile={"passed": True, "details": ""},
    )
    assert report["acceptance_decision"] == "retryable_failure"
    assert any("not present in committed HEAD diff" in issue for issue in report["issues"])


def test_final_acceptance_report_blocks_unexpected_tracked_artifacts() -> None:
    _, _, _, _, _, _, _, _, _, _, _, final_acceptance = _load_runtime_modules()
    report = final_acceptance.build_final_acceptance_report(
        task_file="tasks/076.md",
        validated_required_paths=["agents/lib/final_acceptance.py", "tests/test_run_task_runtime_foundations.py"],
        head_diff_paths=["agents/lib/final_acceptance.py", "tests/test_run_task_runtime_foundations.py", "artifacts/extra.json"],
        working_tree_paths=[],
        validation_profile={"passed": True, "details": ""},
    )
    assert report["acceptance_decision"] == "blocked"
    assert any("Unexpected tracked files remain" in issue for issue in report["issues"])


def test_final_acceptance_report_distinguishes_validation_failure() -> None:
    _, _, _, _, _, _, _, _, _, _, _, final_acceptance = _load_runtime_modules()
    report = final_acceptance.build_final_acceptance_report(
        task_file="tasks/076.md",
        validated_required_paths=["agents/lib/final_acceptance.py"],
        head_diff_paths=["agents/lib/final_acceptance.py"],
        working_tree_paths=[],
        validation_profile={"passed": False, "details": "pytest -q failed"},
    )
    assert report["acceptance_decision"] == "retryable_failure"
    assert any("Authoritative validation profile failed" in issue for issue in report["issues"])


def test_run_task_source_uses_final_acceptance_reviewer() -> None:
    run_task_path = Path(__file__).resolve().parents[1] / "agents" / "run_task.py"
    src = run_task_path.read_text(encoding="utf-8")
    assert "build_final_acceptance_report(" in src
