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
    )


def test_provider_client_delegation(monkeypatch) -> None:
    run_task, _, _, provider_client, _, _, _, _, _, _, _ = _load_runtime_modules()

    def fake_chat(messages, model, provider=None):
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "ok"

    monkeypatch.setattr(provider_client, "chat", fake_chat)
    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "ok"


def test_git_helpers_behavior(monkeypatch) -> None:
    run_task, _, git_ops, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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
    run_task, check_runner, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

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
    run_task, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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
    assert callable(run_task.merge_ready_validation_profile)
    assert callable(run_task.run_merge_ready_validation_profile)


def test_failure_classifier_distinguishes_multiple_categories() -> None:
    _, _, _, _, failure_journal, _, _, _, _, _, _ = _load_runtime_modules()
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
    _, _, _, _, failure_journal, _, _, _, _, _, _ = _load_runtime_modules()
    syntax_plan = failure_journal.build_failure_remediation_plan(
        kind="tests",
        message="SyntaxError: invalid syntax",
        category="python_syntax",
        retry_count=1,
        fingerprint="python_syntax:abc123",
        raw_failure_snippet="SyntaxError: invalid syntax",
    )
    assert syntax_plan["chosen_remediation_path"] == "targeted_syntax_repair"

    harness_plan = failure_journal.build_failure_remediation_plan(
        kind="policy",
        message="Protected meta file(s) in normal bundle lane",
        category="harness_meta_regression",
        retry_count=1,
        fingerprint="harness_meta_regression:def456",
        raw_failure_snippet="Protected meta file(s) in normal bundle lane",
    )
    assert harness_plan["chosen_remediation_path"] == "manual_patch_lane"


def test_failure_artifact_placeholders_are_json(tmp_path: Path) -> None:
    _, _, _, _, _, _, failure_artifacts, _, _, _, _ = _load_runtime_modules()
    out_path = tmp_path / "last_output.json"
    bundle_path = tmp_path / "last_bundle.json"

    failure_artifacts.ensure_truthful_failure_artifacts(
        last_output_path=out_path,
        last_bundle_path=bundle_path,
        create_placeholders=True,
        task_file="tasks/074_orchestrator_batch_runner_cli_and_summary_artifacts.md",
        failure_category="bundle_transport",
        before_model_output=True,
        normal_bundle_attempted=False,
    )

    out_payload = json.loads(out_path.read_text(encoding="utf-8"))
    bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert out_payload["placeholder"] is True
    assert out_payload["artifact_kind"] == "model_output_placeholder"
    assert bundle_payload["artifact_kind"] == "file_bundle_placeholder"
    assert bundle_payload["kind"] == "file_bundle"


def test_batch_state_runtime_artifact_placeholder_blocks_continue_gate(tmp_path: Path) -> None:
    run_task, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    out_path = tmp_path / "last_output.json"
    bundle_path = tmp_path / "last_bundle.json"

    run_task._emit_failure_artifact_messages(
        out_path,
        bundle_path,
        create_placeholders=True,
        task_file="tasks/075_orchestrator_backlog_execution_end_to_end_proof.md",
        failure_category="blocked",
        before_model_output=True,
        reason="e2e proof blocked before model output",
    )

    out_payload = json.loads(out_path.read_text(encoding="utf-8"))
    checkpoint = out_payload["batch_checkpoint"]
    assert checkpoint["next_task_may_proceed"] is False
    assert checkpoint["transition"] in {"blocked", "failed_before_model_output"}
    if isinstance(out_payload.get("batch_state"), dict):
        assert out_payload["batch_state"]["next_task_may_proceed"] is False
        assert out_payload["batch_state"]["checkpoint_transition"] == checkpoint["transition"]


def test_shell_router_seam_registry_exposes_expected_keys() -> None:
    _, _, _, _, _, _, _, shell_router, _, _, _ = _load_runtime_modules()
    registry = shell_router.shell_seam_exports()
    assert "bootstrap" in registry
    assert "failure_journal" in registry
    assert "validator_runner" in registry
    assert "shell_router" in registry
