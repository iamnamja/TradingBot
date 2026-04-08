from __future__ import annotations

import importlib
import sys
from pathlib import Path


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
    multi_agent_contract = importlib.import_module("agents.lib.multi_agent_contract")
    final_acceptance = importlib.import_module("agents.lib.final_acceptance")
    batch_executor = importlib.import_module("agents.lib.batch_executor")
    controller_strict_mode = importlib.import_module("agents.lib.controller_strict_mode")
    multi_agent_loop = importlib.import_module("agents.lib.multi_agent_loop")
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
        multi_agent_contract,
        final_acceptance,
        batch_executor,
        controller_strict_mode,
        multi_agent_loop,
    )


def test_provider_client_delegation(monkeypatch) -> None:
    run_task, _, _, provider_client, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    def fake_chat(messages, model, provider=None):
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "ok"

    monkeypatch.setattr(provider_client, "chat", fake_chat)
    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "ok"


def test_git_helpers_behavior(monkeypatch) -> None:
    run_task, _, git_ops, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    calls: list[tuple[list[str], bool]] = []

    class _Result:
        def __init__(self):
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""

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
        return _Result()

    monkeypatch.setattr(git_ops, "capture", fake_capture)
    monkeypatch.setattr(git_ops, "run", fake_run)
    run_task.ensure_clean_worktree()
    run_task.ensure_branch("feature-x")
    assert any(cmd == ["git", "checkout", "-b", "feature-x"] for cmd, _ in calls) or any(
        cmd == ["git", "checkout", "-B", "feature-x"] for cmd, _ in calls
    )


def test_check_runner_summary(monkeypatch) -> None:
    run_task, check_runner, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    class _CP:
        def __init__(self, returncode: int, stdout: str, stderr: str):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_capture_result(cmd):
        if cmd == ["ruff", "check", "."]:
            return _CP(returncode=0, stdout="lint out\n", stderr="")
        if cmd == ["pytest", "-q"]:
            return _CP(returncode=1, stdout="test out\n", stderr="test err\n")
        raise AssertionError(cmd)

    monkeypatch.setattr(check_runner, "capture_result", fake_capture_result)
    ok, text = run_task.run_checks()
    assert ok is False
    assert "=== pytest -q ===" in text
    assert "test out" in text


def test_public_surface_still_available() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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
    assert callable(run_task.build_final_acceptance_retry_feedback)
    assert callable(run_task.report_final_acceptance_failure)
    assert callable(run_task.build_controller_failure_digest)
    assert callable(run_task.build_controller_repair_context)
    assert callable(run_task.choose_repair_strategy)
    assert callable(run_task.format_repair_strategy)
    assert callable(run_task.build_controller_test_failure_appendix)
    assert callable(run_task.execute_batch_loop)
    assert callable(run_task.accepted_task_pr_merge_flow)
    assert callable(run_task.canonical_required_check_truth)
    assert callable(run_task.evaluate_verification_authority)
    assert callable(run_task.evaluate_hosted_authority_operational_convergence)
    assert callable(run_task.canonical_repo_enforcement_truth)
    assert callable(run_task.probe_repo_required_check_enforcement)
    assert callable(run_task.evaluate_repo_required_check_convergence)
    assert callable(run_task.report_branch_push_ready)
    assert callable(run_task.restore_file_snapshot_subset)
    assert callable(run_task.build_last_green_subset_preservation_plan)
    assert callable(run_task.write_last_green_subset_artifact)
    assert callable(run_task.build_controller_strict_mode_context)
    assert callable(run_task.describe_controller_strict_mode)
    assert callable(run_task.resolve_project_contract)
    assert callable(run_task.project_validation_matrix)
    assert callable(run_task.build_project_validation_plan)
    assert callable(run_task.project_verification_authority_profile)
    assert callable(run_task.project_repo_check_contract)
    assert callable(run_task.evaluate_project_verification_authority)


def test_project_merge_helpers_are_available() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    contract = run_task.resolve_project_contract('tradingbot_monorepo')
    merge_contract = run_task.project_merge_eligibility_contract(contract)
    required_truth = run_task.canonical_required_check_truth(
        verification_authority_profile='local_plus_required_ci',
        repo_check_contract=run_task.project_repo_check_contract(contract),
        required_checks_discovered=False,
        hosted_checks_reported=False,
        hosted_authority_probe_status='misconfigured',
    )
    convergence = run_task.evaluate_hosted_authority_convergence(
        verification_authority_profile='local_plus_required_ci',
        repo_check_contract=run_task.project_repo_check_contract(contract),
        required_check_truth=required_truth,
    )
    operational = run_task.evaluate_hosted_authority_operational_convergence(
        verification_authority_profile='local_plus_required_ci',
        repo_check_contract=run_task.project_repo_check_contract(contract),
        required_check_truth=required_truth,
    )

    assert merge_contract['project_id'] == 'tradingbot_monorepo'
    assert merge_contract['merge_requires_hosted_authority'] is True
    assert convergence['hosted_authority_converged'] is False
    assert operational['unattended_execution_ready'] is False
    assert operational['operational_convergence_reason'] == 'hosted_checks_not_reporting'



def test_project_contract_contains_workspace_and_isolation_namespaces() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    contract = run_task.resolve_project_contract("generic_python_external")

    assert isinstance(contract["workspace_root"], str)
    assert isinstance(contract["branch_namespace"], str)
    assert isinstance(contract["state_namespace"], str)
    assert isinstance(contract["carry_forward_memory_namespace"], str)


def test_task_136_resilience_public_surface_remains_available() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    assert callable(run_task.evaluate_proof_task_admission)
    assert callable(run_task.report_proof_task_admission_failure)
    assert callable(run_task.classify_bundle_transport_failure)
    assert callable(run_task.extract_missing_deliverable_evidence)
    assert callable(run_task.build_missing_deliverable_retry_feedback)
    assert callable(run_task.restore_file_snapshot_subset)
    assert callable(run_task.build_last_green_subset_preservation_plan)
    assert callable(run_task.write_last_green_subset_artifact)


def test_task_137_github_enforcement_helpers_are_available() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    repo_contract = run_task.project_repo_check_contract(run_task.resolve_project_contract("tradingbot_monorepo"))
    enforcement_truth = run_task.canonical_repo_enforcement_truth(
        repo_check_contract=repo_contract,
        enforcement_probe_available=True,
        enforcement_probe_status="required_check_context_missing",
        enforcement_source="github_branch_rules",
        required_status_checks_rule_present=True,
        required_status_check_contexts=("wrong-check",),
    )
    convergence = run_task.evaluate_repo_required_check_convergence(
        repo_check_contract=repo_contract,
        repo_enforcement_truth=enforcement_truth,
    )
    operational = run_task.evaluate_hosted_authority_operational_convergence(
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=repo_contract,
        required_check_truth=run_task.canonical_required_check_truth(
            verification_authority_profile="local_plus_required_ci",
            repo_check_contract=repo_contract,
            required_checks_discovered=True,
            hosted_checks_reported=True,
            required_checks_passed=True,
            hosted_authority_probe_status="satisfied",
        ),
        repo_enforcement_truth=enforcement_truth,
    )

    assert repo_contract["repo_default_branch"] == "main"
    assert convergence["repo_required_check_enforcement_reason"] == "required_check_context_missing"
    assert operational["operational_convergence_reason"] == "required_check_enforcement_context_mismatch"
