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
    assert callable(run_task.choose_repair_strategy)
    assert callable(run_task.format_repair_strategy)
    assert callable(run_task.build_controller_test_failure_appendix)
    assert callable(run_task.execute_batch_loop)
    assert callable(run_task.accepted_task_pr_merge_flow)
    assert callable(run_task.canonical_required_check_truth)
    assert callable(run_task.evaluate_verification_authority)
    assert callable(run_task.report_branch_push_ready)
    assert callable(run_task.build_controller_strict_mode_context)
    assert callable(run_task.describe_controller_strict_mode)
    assert callable(run_task.proof_sync_contract_snapshot)
    assert callable(run_task.validate_proof_sync_contract)


def test_multi_agent_loop_surface_exposes_execute_cycle_symbol() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, multi_agent_loop = _load_runtime_modules()
    assert callable(run_task.execute_multi_agent_loop)
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



def test_proof_sync_contract_snapshot_exposes_expected_guard_surface() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, multi_agent_contract, _, _, _, _ = _load_runtime_modules()
    snapshot = run_task.proof_sync_contract_snapshot()

    assert snapshot["run_task_exports"]
    assert "execute_multi_agent_loop" in snapshot["run_task_exports"]
    assert "run_multi_agent_controller_cycle" in snapshot["multi_agent_loop_exports"]
    assert "processed_task_ids" in snapshot["compatibility_result_fields"]
    assert "controller_decision" in snapshot["canonical_result_fields"]

    result = run_task.validate_proof_sync_contract(
        run_task_exports=snapshot["run_task_exports"],
        multi_agent_loop_exports=snapshot["multi_agent_loop_exports"],
        compatibility_result={"processed_task_ids": [], "verification_authority": "local_only", "controller_final_decision": "continue", "runtime_portability_scope": "python_only"},
        canonical_result={"builder_artifact": {}, "verifier_artifact": {}, "controller_decision": {}, "role_handoff_state": {}},
        manifest_examples=[{"task_path": "tasks/001.md"}, {"path": "tasks/002.md", "depends_on": ["tasks/001.md"]}],
        role_snapshot=multi_agent_contract.multi_agent_contract_snapshot(),
        boundary_snapshot=multi_agent_contract.orchestrator_package_boundary_snapshot(),
        claim_texts=[Path("README.md").read_text(encoding="utf-8"), Path("docs/ORCHESTRATOR_PRODUCT_SPEC.md").read_text(encoding="utf-8"), Path("docs/TRADINGBOT_PROJECT_STATE.md").read_text(encoding="utf-8")],
    )
    assert result["ok"] is True


def test_proof_sync_contract_validator_flags_missing_exports_and_overclaims() -> None:
    run_task, *_ = _load_runtime_modules()
    result = run_task.validate_proof_sync_contract(
        run_task_exports=["execute_multi_agent_loop"],
        multi_agent_loop_exports=["execute_multi_agent_loop"],
        compatibility_result={"processed_task_ids": []},
        canonical_result={"controller_decision": {}},
        manifest_examples=[{"unexpected": "x"}],
        role_snapshot={"roles": ["controller", "builder", "verifier"]},
        boundary_snapshot={"product_name": "orchestrator"},
        claim_texts=["This repo now provides broad unattended scheduler autonomy and full standalone extraction completion."],
    )
    assert result["ok"] is False
    assert result["missing_run_task_exports"]
    assert result["missing_multi_agent_loop_exports"]
    assert result["manifest_issues"]
    assert result["claim_guard_issues"]



def test_supervised_mixed_manifest_reproof_surface_is_available_and_bounded() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, multi_agent_loop = _load_runtime_modules()

    def choose_next_role(ctx: dict[str, object]) -> str:
        phase = str(ctx.get("phase") or "")
        if phase == "build":
            return "builder"
        if phase == "verify":
            return "verifier"
        return "controller"

    def run_role(role: str, ctx: dict[str, object]) -> dict[str, object]:
        if role == "builder":
            return {"status": "built", "task_path": str(ctx["task_path"])}
        if role == "verifier":
            return {"accepted": True, "verification_authority": "local_only", "task_path": str(ctx["task_path"])}
        return {"controller_final_decision": "continue", "post_task_decision": "continue"}

    result = multi_agent_loop.execute_multi_agent_loop(
        task_manifest={
            "tasks": [
                {"task_path": "tasks/089_orchestrator_hardened_autonomous_short_manifest_proof.md", "task_family": "proof_docs"},
                {"task_path": "tasks/106_orchestrator_external_workspace_bootstrap_recovery_proof.md", "task_family": "bootstrap"},
                {"task_path": "tasks/107_orchestrator_supervised_mixed_manifest_autonomy_reproof.md", "task_family": "consumer_facing"},
            ]
        },
        choose_next_role=choose_next_role,
        run_role=run_role,
    )

    normalized = run_task.normalize_multi_agent_loop_result(result)
    assert normalized["count"] == 3
    assert normalized["runtime_portability_scope"] == "python_only"
