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
    run_task, check_runner, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

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
    assert callable(run_task.classify_collection_failure)
    assert callable(run_task.is_collection_failure)
    assert callable(run_task.choose_repair_strategy)
    assert callable(run_task.format_repair_strategy)
    assert callable(run_task.build_controller_test_failure_appendix)
    assert callable(run_task.execute_batch_loop)
    assert callable(run_task.accepted_task_pr_merge_flow)
    assert callable(run_task.canonical_required_check_truth)
    assert callable(run_task.evaluate_verification_authority)
    assert callable(run_task.report_branch_push_ready)
    assert callable(run_task.wait_for_required_checks)
    assert callable(run_task.coerce_verification_authority_profile)
    assert callable(run_task.build_controller_strict_mode_context)
    assert callable(run_task.describe_controller_strict_mode)


def test_multi_agent_loop_surface_exposes_execute_cycle_symbol() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, multi_agent_loop = _load_runtime_modules()
    assert callable(run_task.execute_multi_agent_loop)
    assert callable(run_task.normalize_manifest_entry_schema)
    assert callable(run_task.normalize_multi_agent_loop_result)
    assert hasattr(multi_agent_loop, "execute_multi_agent_loop")
    assert callable(multi_agent_loop.execute_multi_agent_loop)


def test_multi_agent_contract_snapshot_remains_stable_and_explicitly_bounded() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, multi_agent_contract, _, _, _, _ = _load_runtime_modules()
    snapshot = multi_agent_contract.multi_agent_contract_snapshot()

    assert callable(run_task.multi_agent_contract_snapshot)
    assert snapshot["roles"] == ["controller", "builder", "verifier"]
    assert snapshot["sequential_role_execution_only"] is True
    assert snapshot["controller_authority_over_next_role"] is True


def test_orchestrator_package_boundary_snapshot_stays_in_extraction_prep_posture() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, multi_agent_contract, _, _, _, _ = _load_runtime_modules()
    boundary = multi_agent_contract.orchestrator_package_boundary_snapshot()

    assert callable(run_task.orchestrator_package_boundary_snapshot)
    assert boundary["product_name"] == "orchestrator"
    assert boundary["operates_inside_monorepo"] is True
    assert boundary["full_standalone_extraction_completed"] is False
    assert "tradingbot" in boundary["supported_consumers"]
    assert "generic_python" in boundary["supported_consumers"]


def test_collection_failure_helpers_expose_narrow_first_class_lane() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    message = "ERROR collecting tests/test_multi_project_adapters.py\nImportError while importing test module\ncannot import name 'run_multi_agent_controller_cycle'"

    assert run_task.classify_collection_failure(kind="tests", message=message) == "collection_import_failure"
    assert run_task.is_collection_failure(kind="tests", message=message) is True

    route = run_task.choose_repair_strategy(kind="tests", message=message, category="collection_import_failure")
    assert route["repair_strategy"] == "collection_import_contract_repair"
    assert route["remediation_lane"] == "builder"


def test_multi_agent_result_normalization_keeps_bounded_proof_fields() -> None:
    run_task, *_ = _load_runtime_modules()
    normalized = run_task.normalize_multi_agent_loop_result({
        "processed_task_ids": ["alpha", "beta"],
        "verification_authority": "local_only",
        "controller_final_decision": "continue",
    })
    assert normalized["processed_task_ids"] == ["alpha", "beta"]
    assert normalized["count"] == 2
    assert normalized["runtime_portability_scope"] == "python_only"
