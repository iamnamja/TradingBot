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
        raw_failure_snippet="SyntaxError",
    )
    harness_plan = failure_journal.build_failure_remediation_plan(
        kind="policy",
        message="Protected meta file(s) in normal bundle lane",
        category="harness_meta_regression",
        retry_count=1,
        fingerprint="harness_meta_regression:def456",
        raw_failure_snippet="Protected meta",
    )

    assert syntax_plan["recommended_next_action"] == "retry_with_targeted_fix"
    assert syntax_plan["chosen_remediation_path"] == "targeted_syntax_repair"
    assert harness_plan["recommended_next_action"] == "manual_patch"
    assert harness_plan["chosen_remediation_path"] == "manual_patch_lane"


def test_task_contract_runtime_helpers_exposed() -> None:
    _, _, _, _, _, task_contracts, _, _, _, _, _ = _load_runtime_modules()
    assert hasattr(task_contracts, "classify_branch_diff_paths")
    assert hasattr(task_contracts, "committed_state_parity_issues")
    assert callable(task_contracts.classify_branch_diff_paths)
    assert callable(task_contracts.committed_state_parity_issues)


def test_final_success_blocked_when_required_only_in_worktree_not_head() -> None:
    _, _, _, _, _, task_contracts, _, _, _, _, _ = _load_runtime_modules()

    required = ["agents/lib/task_contracts.py", "tests/test_run_task_runtime_foundations.py"]
    head_diff = ["tests/test_run_task_runtime_foundations.py"]
    worktree = ["agents/lib/task_contracts.py"]

    issues = task_contracts.committed_state_parity_issues(
        validated_required_paths=required,
        head_diff_paths=head_diff,
        working_tree_paths=worktree,
    )

    assert any("not present in committed HEAD diff" in issue for issue in issues)
    assert any("exist only in working tree" in issue for issue in issues)


def test_final_success_blocked_when_unexpected_tracked_artifact_in_branch_diff() -> None:
    _, _, _, _, _, task_contracts, _, _, _, _, _ = _load_runtime_modules()

    required = ["agents/lib/task_contracts.py", "tests/test_run_task_runtime_foundations.py"]
    head_diff = [
        "agents/lib/task_contracts.py",
        "tests/test_run_task_runtime_foundations.py",
        "artifacts/last_output.json",
    ]

    issues = task_contracts.committed_state_parity_issues(
        validated_required_paths=required,
        head_diff_paths=head_diff,
        working_tree_paths=[],
    )

    assert any("Unexpected tracked files remain in committed HEAD diff" in issue for issue in issues)
    assert any("artifacts/last_output.json" in issue for issue in issues)


def test_final_success_allowed_only_when_head_matches_validated_state() -> None:
    _, _, _, _, _, task_contracts, _, _, _, _, _ = _load_runtime_modules()

    required = ["agents/lib/task_contracts.py", "tests/test_run_task_runtime_foundations.py"]
    head_diff = list(required)

    issues = task_contracts.committed_state_parity_issues(
        validated_required_paths=required,
        head_diff_paths=head_diff,
        working_tree_paths=[],
    )

    assert issues == []


def test_branch_diff_classification_separates_required_and_unexpected() -> None:
    _, _, _, _, _, task_contracts, _, _, _, _, _ = _load_runtime_modules()

    classification = task_contracts.classify_branch_diff_paths(
        branch_diff_paths=[
            "agents/lib/task_contracts.py",
            "tests/test_run_task_runtime_foundations.py",
            "artifacts/extra.json",
        ],
        required_paths=[
            "agents/lib/task_contracts.py",
            "tests/test_run_task_runtime_foundations.py",
            "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md",
        ],
    )

    assert classification["required_present"] == [
        "agents/lib/task_contracts.py",
        "tests/test_run_task_runtime_foundations.py",
    ]
    assert classification["missing_required"] == ["docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"]
    assert classification["unexpected"] == ["artifacts/extra.json"]


def test_failure_artifact_payload_handles_parity_gate_categories(tmp_path: Path) -> None:
    _, _, _, _, _, _, failure_artifacts, _, _, _, _ = _load_runtime_modules()

    out_path = tmp_path / "last_output.json"
    bundle_path = tmp_path / "last_bundle.json"

    failure_artifacts.ensure_truthful_failure_artifacts(
        last_output_path=out_path,
        last_bundle_path=bundle_path,
        create_placeholders=True,
        task_file="tasks/074c.md",
        failure_category="merge_ready_validation",
        before_model_output=True,
        normal_bundle_attempted=True,
        reason="committed-state parity failed",
    )

    output_payload = json.loads(out_path.read_text(encoding="utf-8"))
    bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert output_payload["placeholder"] is True
    assert output_payload["failure_category"] == "merge_ready_validation"
    assert bundle_payload["kind"] == "file_bundle"
    assert bundle_payload["files"] == []
