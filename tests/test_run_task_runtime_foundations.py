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
    assert callable(run_task.build_controller_test_failure_appendix)
    assert callable(run_task.execute_batch_loop)
    assert callable(run_task.accepted_task_pr_merge_flow)
    assert callable(run_task.report_branch_push_ready)
    assert callable(run_task.build_controller_strict_mode_context)
    assert callable(run_task.describe_controller_strict_mode)
    assert callable(run_task.controller_strict_preapply_issues)
    assert callable(run_task.format_controller_strict_preapply_issues)
    assert callable(run_task.run_controller_strict_checks)
    assert callable(run_task.strict_validation_profile)
    assert callable(run_task.multi_agent_contract_snapshot)
    assert callable(run_task.canonical_role_handoff_state)
    assert callable(run_task.resume_role_handoff_state)
    assert callable(run_task.controller_decides_next_role)
    assert callable(run_task.multi_agent_task_context)
    assert callable(run_task.build_builder_patch_attempt)
    assert callable(run_task.build_verifier_evidence_bundle)
    assert callable(run_task.build_multi_agent_controller_decision)
    assert callable(run_task.execute_multi_agent_loop)


def test_run_task_runtime_contract_modules_share_canonical_surface() -> None:
    (_, _, _, _, failure_journal, _, _, _, _, batch_state, task_queue, controller_contract, _, _, batch_executor, _, _) = _load_runtime_modules()
    assert task_queue.BatchPostTaskDecision is controller_contract.BatchPostTaskDecision
    assert batch_state.BatchStatus is controller_contract.BatchStatus
    assert batch_executor.ResumeMode is controller_contract.ResumeMode
    assert failure_journal.POLICY_BLOCKED_FAILURE_CATEGORY == controller_contract.POLICY_BLOCKED_FAILURE_CATEGORY
    assert "build_controller_test_failure_appendix" in controller_contract.CONTROLLER_RUNTIME_DELEGATE_SURFACES
    assert "describe_controller_strict_mode" in controller_contract.CONTROLLER_RUNTIME_DELEGATE_SURFACES
    assert "multi_agent_contract_snapshot" in controller_contract.CONTROLLER_RUNTIME_DELEGATE_SURFACES
    assert "agents/lib/multi_agent_contract.py" in controller_contract.CONTROLLER_FAMILY_FILES


def test_failure_classifier_distinguishes_multiple_categories() -> None:
    _, _, _, _, failure_journal, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
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
    (_, _, _, _, _, _, _, _, _, batch_state, task_queue, _, _, _, batch_executor, _, _) = _load_runtime_modules()

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


def test_run_task_delegates_new_controller_repair_appendix_wrapper(monkeypatch) -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()
    controller_repair = importlib.import_module("agents.lib.controller_repair")

    def fake_appendix(**kwargs):
        assert kwargs["details"] == "boom"
        assert kwargs["semantic_hints"] == "hint"
        return "delegated appendix"

    monkeypatch.setattr(controller_repair, "build_controller_test_failure_appendix", fake_appendix)
    assert run_task.build_controller_test_failure_appendix(details="boom", semantic_hints="hint") == "delegated appendix"


def test_run_task_delegates_new_final_acceptance_retry_feedback_wrapper(monkeypatch) -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, final_acceptance, _, _, _ = _load_runtime_modules()

    def fake_feedback(report):
        assert report == {"acceptance_decision": "retryable_failure"}
        return {"feedback_text": "delegated feedback", "should_stop": False}

    monkeypatch.setattr(final_acceptance, "build_final_acceptance_retry_feedback", fake_feedback)
    assert run_task.build_final_acceptance_retry_feedback({"acceptance_decision": "retryable_failure"}) == {"feedback_text": "delegated feedback", "should_stop": False}


def test_run_task_delegates_new_controller_strict_mode_wrappers(monkeypatch) -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, controller_strict_mode, _ = _load_runtime_modules()

    def fake_describe(*, required_paths=None, task_file=""):
        assert required_paths == ["agents/run_task.py"]
        assert task_file == "tasks/088_orchestrator_controller_decomposition_fourth_extraction.md"
        return {"enabled": True, "status_lines": ["delegated strict mode"]}

    def fake_profile(result):
        assert result == {"focused_ok": True, "lint_ok": True, "test_ok": True, "output_text": ""}
        return {"passed": True, "details": "delegated"}

    def fake_format(issues):
        assert issues == ["issue"]
        return "delegated formatting"

    monkeypatch.setattr(controller_strict_mode, "describe_controller_strict_mode", fake_describe)
    monkeypatch.setattr(controller_strict_mode, "strict_validation_profile", fake_profile)
    monkeypatch.setattr(controller_strict_mode, "format_controller_strict_preapply_issues", fake_format)

    described = run_task.describe_controller_strict_mode(
        required_paths=["agents/run_task.py"],
        task_file="tasks/088_orchestrator_controller_decomposition_fourth_extraction.md",
    )
    assert described == {"enabled": True, "status_lines": ["delegated strict mode"]}
    assert run_task.strict_validation_profile({"focused_ok": True, "lint_ok": True, "test_ok": True, "output_text": ""}) == {"passed": True, "details": "delegated"}
    assert run_task.format_controller_strict_preapply_issues(["issue"]) == "delegated formatting"


def test_controller_repair_context_names_semantic_drift_surfaces() -> None:
    run_task, _, _, _, failure_journal, _, _, _, _, _, _, _, _, final_acceptance, _, controller_strict_mode, _ = _load_runtime_modules()

    details = (
        "________________ test_controller_contract_guard __________________\n"
        "E AssertionError: assert 'continue' == 'failed_checks'\n"
        "E KeyError: 'resume_gate'\n"
        "E AttributeError: module 'agents.run_task' has no attribute 'build_controller_failure_digest'\n"
        "tests/test_run_task_runtime_foundations.py:200: AssertionError\n"
    )
    digest = run_task.build_controller_failure_digest(
        kind="tests",
        message=details,
        category="tests",
        touched_files=["agents/run_task.py", "agents/lib/controller_contract.py"],
        task_file="tasks/086_orchestrator_semantic_failure_digest_and_controller_repair_context.md",
    )
    assert digest["decision_mismatches"] == [{"actual": "continue", "expected": "failed_checks"}]
    assert digest["missing_truth_fields"] == ["resume_gate"]
    assert digest["missing_exports"] == ["build_controller_failure_digest"]

    context = run_task.build_controller_repair_context(
        kind="tests",
        message=details,
        category="tests",
        touched_files=["agents/run_task.py", "agents/lib/controller_contract.py"],
        task_file="tasks/086_orchestrator_semantic_failure_digest_and_controller_repair_context.md",
    )
    prompt = str(context["repair_prompt"])
    assert "Controller semantic failure digest" in prompt
    assert "decision_mismatches" in prompt
    assert "missing_truth_fields" in prompt
    assert "missing_exports" in prompt

    journal_digest = failure_journal.build_semantic_failure_digest(
        kind="tests",
        message=details,
        category="tests",
        touched_files=["agents/run_task.py"],
        task_file="tasks/086_orchestrator_semantic_failure_digest_and_controller_repair_context.md",
    )
    assert journal_digest["is_controller_failure"] is True

    report = final_acceptance.build_final_acceptance_report(
        task_file="tasks/086_orchestrator_semantic_failure_digest_and_controller_repair_context.md",
        validated_required_paths=["agents/run_task.py", "agents/lib/controller_contract.py"],
        head_diff_paths=["agents/run_task.py", "agents/lib/controller_contract.py"],
        working_tree_paths=["agents/run_task.py", "agents/lib/controller_contract.py"],
        validation_profile={"passed": False, "details": details},
    )
    self_heal = final_acceptance.build_acceptance_self_heal_context(report)
    assert self_heal["semantic_failure_digest"]["decision_mismatches"] == [{"actual": "continue", "expected": "failed_checks"}]
    assert "Semantic controller repair context:" in str(self_heal["repair_prompt"])


def test_controller_task_shape_activates_strict_mode() -> None:
    run_task, _, _, _, _, task_contracts, _, _, _, _, _, controller_contract, _, _, _, controller_strict_mode, _ = _load_runtime_modules()

    assert task_contracts.task_touches_controller_core(["agents/run_task.py", "docs/TRADINGBOT_PROJECT_STATE.md"]) is True
    context = run_task.build_controller_strict_mode_context(
        required_paths=["agents/run_task.py", "docs/TRADINGBOT_PROJECT_STATE.md"],
        task_file="tasks/087_orchestrator_controller_task_strict_mode_and_patch_quality_gate.md",
    )
    assert context["enabled"] is True
    assert context["strict_targets_touched"] == ["agents/run_task.py"]
    assert context["focused_test_paths"] == list(controller_contract.CONTROLLER_PROOF_TEST_PATHS)
    assert controller_strict_mode.controller_strict_mode_directives(context)


def test_controller_patch_quality_gate_rejects_obvious_minified_bundle() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    issues = run_task.controller_strict_preapply_issues(
        {
            "agents/run_task.py": (
                "import os, sys\n"
                "import json, re\n"
                "def bad(): a=1; b=2; c=3; print(a+b+c)\n"
                "def worse(): x=1; y=2; z=3; print(x+y+z)\n"
                "def noisy(): foo=1; bar=2; baz=3; return foo+bar+baz\n"
            )
        },
        touched_paths=["agents/run_task.py"],
    )
    assert issues
    assert any("controller strict mode rejected" in issue for issue in issues)


def test_controller_strict_checks_defer_docs_claims_until_proof_tests_are_green(monkeypatch) -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, controller_strict_mode, _ = _load_runtime_modules()

    commands: list[list[str]] = []

    def fake_capture_result(cmd: list[str]):
        commands.append(cmd)
        if cmd[:2] == ["pytest", "-q"] and "tests/test_controller_contract.py" in cmd:
            return SimpleNamespace(returncode=1, stdout="focused fail\n", stderr="")
        raise AssertionError(cmd)

    result = controller_strict_mode.run_controller_strict_checks(
        capture_result=fake_capture_result,
        changed_paths=["README.md", "docs/TRADINGBOT_PROJECT_STATE.md"],
    )

    assert commands == [["pytest", "-q", "tests/test_controller_contract.py", "tests/test_run_task_runtime_foundations.py", "tests/test_task_queue.py"]]
    assert result["controller_proof_tests_passed"] is False
    assert result["proof_claims_deferred"] is True
    assert "deferred until focused controller proof tests are green" in result["output_text"]

    monkeypatch.setattr(run_task, "capture_result", fake_capture_result)
    wrapped = run_task.run_controller_strict_checks(changed_paths=["README.md"])
    assert wrapped["proof_claims_deferred"] is True


def test_controller_strict_checks_allow_proof_claims_once_focused_surface_is_green(monkeypatch) -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, controller_strict_mode, _ = _load_runtime_modules()

    commands: list[list[str]] = []

    def fake_capture_result(cmd: list[str]):
        commands.append(cmd)
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    result = controller_strict_mode.run_controller_strict_checks(
        capture_result=fake_capture_result,
        changed_paths=["README.md", "docs/TRADINGBOT_PROJECT_STATE.md"],
    )

    assert commands == [
        ["pytest", "-q", "tests/test_controller_contract.py", "tests/test_run_task_runtime_foundations.py", "tests/test_task_queue.py"],
        ["ruff", "check", "."],
        ["pytest", "-q"],
    ]
    assert result["controller_proof_tests_passed"] is True
    assert result["proof_claims_deferred"] is False
    assert result["proof_claims_deferred_message"] == ""

    monkeypatch.setattr(run_task, "capture_result", fake_capture_result)
    wrapped = run_task.run_controller_strict_checks(changed_paths=["README.md", "docs/TRADINGBOT_PROJECT_STATE.md"])
    assert wrapped["controller_proof_tests_passed"] is True
    assert wrapped["proof_claims_deferred"] is False


def test_autonomous_backlog_runner_proof_capabilities_remain_narrow_and_hardened() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    assert run_task.autonomous_backlog_runner_proof_capabilities() == {
        "ordinary_manifest_autonomous_proof": True,
        "retryable_self_heal_without_raw_reexecute": True,
        "merge_posture_stop_honesty": True,
        "resume_after_merge_skip_semantics": True,
    }



def test_run_task_exposes_multi_agent_role_contract_and_task_context() -> None:
    run_task, _, _, _, _, task_contracts, _, _, _, _, _, _, multi_agent_contract, _, _, _, multi_agent_loop = _load_runtime_modules()

    assert run_task.multi_agent_contract_snapshot() == multi_agent_contract.multi_agent_contract_snapshot()
    role_state = run_task.canonical_role_handoff_state(
        active_role="controller",
        handoff_reason="controller_selected_builder",
        controller_next_role_decision="builder",
        role_outcome="controller_routed",
    )
    assert role_state["active_role"] == "controller"
    assert role_state["controller_next_role_decision"] == "builder"
    resumed = run_task.resume_role_handoff_state(role_state)
    assert resumed["pending_role"] == "builder"
    assert run_task.controller_decides_next_role(
        current_role="controller",
        proposed_next_role="builder",
        proposed_by_role="controller",
    ) == "builder"

    context = run_task.multi_agent_task_context(["agents/run_task.py"])
    assert context == task_contracts.multi_agent_task_context(["agents/run_task.py"])
    assert context["controller_authority_over_next_role"] is True
    assert context["sequential_role_execution_only"] is True


def test_run_task_exposes_canonical_multi_agent_loop_with_distinct_role_artifacts() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, multi_agent_loop = _load_runtime_modules()

    def builder_step(role_state):
        assert role_state["active_role"] == "builder"
        return {"changed_files": ["agents/run_task.py"], "summary": "builder patch ready"}

    def verifier_step(builder_artifact, role_state):
        assert builder_artifact["role"] == "builder"
        assert role_state["active_role"] == "verifier"
        return {
            "validator_ok": True,
            "validator_note": "focused/full validation passed",
            "focused_results": ["tests/test_run_task_runtime_foundations.py"],
            "full_results": ["pytest -q"],
            "acceptance_report": {
                "acceptance_decision": "accepted",
                "post_task_decision": "continue",
                "next_task_may_proceed": True,
                "note": "accepted",
            },
        }

    result = run_task.execute_multi_agent_loop(
        task_path="tasks/091_orchestrator_builder_verifier_controller_loop.md",
        builder_step=builder_step,
        verifier_step=verifier_step,
    )

    assert result == multi_agent_loop.execute_multi_agent_loop(
        task_path="tasks/091_orchestrator_builder_verifier_controller_loop.md",
        builder_step=builder_step,
        verifier_step=verifier_step,
    )
    assert result["role_trace"] == ["controller", "builder", "controller", "verifier", "controller"]
    assert result["builder_artifact"]["artifact_kind"] == "builder_patch_attempt"
    assert result["verifier_artifact"]["artifact_kind"] == "verifier_evidence_bundle"
    assert result["builder_artifact"]["role"] == "builder"
    assert result["verifier_artifact"]["role"] == "verifier"
    assert result["controller_decision"]["role"] == "controller"
    assert result["controller_decision"]["action"] == "advance"
    assert result["controller_decision"]["final_authority_role"] == "controller"
    assert result["failure_journal_context"]["controller_action"] == "advance"


def test_multi_agent_loop_failed_verifier_result_requests_repair_without_blurring_roles() -> None:
    run_task, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = _load_runtime_modules()

    def builder_step(_role_state):
        return {"changed_files": ["agents/lib/final_acceptance.py"], "summary": "builder patch ready"}

    def verifier_step(_builder_artifact, _role_state):
        return {
            "validator_ok": False,
            "validator_note": "focused validation failed",
            "focused_results": ["tests/test_task_queue.py::test_x"],
            "acceptance_report": {
                "acceptance_decision": "retryable_failure",
                "post_task_decision": "stop",
                "next_task_may_proceed": False,
                "note": "repair and retry",
            },
        }

    result = run_task.execute_multi_agent_loop(
        task_path="tasks/091_orchestrator_builder_verifier_controller_loop.md",
        builder_step=builder_step,
        verifier_step=verifier_step,
    )

    assert result["builder_artifact"]["summary"] == "builder patch ready"
    assert result["verifier_artifact"]["summary"] != result["builder_artifact"]["summary"]
    assert result["verifier_artifact"]["verdict"] == "fail"
    assert result["controller_decision"]["action"] == "repair"
    assert result["controller_decision"]["next_task_may_proceed"] is False
