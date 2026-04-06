from __future__ import annotations

import importlib
import sys
from pathlib import Path



def _bootstrap_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)



def _load(name: str):
    _bootstrap_repo_root()
    return importlib.import_module(name)



def test_controller_contract_snapshot_is_canonical() -> None:
    contract = _load("agents.lib.controller_contract")
    snapshot = contract.controller_contract_snapshot()

    assert snapshot["acceptance_decisions"] == [
        "accepted",
        "retryable_failure",
        "manual_patch",
        "blocked",
    ]
    assert snapshot["post_task_decisions"] == [
        "continue",
        "stop",
        "manual_patch",
        "blocked",
        "failed_merge",
        "failed_checks",
        "failed_reset",
    ]
    assert snapshot["resume_modes"] == [
        "default",
        "resume_same_task",
        "resume_next",
        "resume_after_merge",
        "resume_after_manual_resolution",
    ]
    assert "acceptance_decision" in snapshot["checkpoint_truth_fields"]
    assert "resume_target_task_path" in snapshot["resume_metadata_fields"]

    assert snapshot["controller_strict_mode_paths"] == [
        "agents/run_task.py",
        "agents/lib/controller_contract.py",
        "agents/lib/batch_executor.py",
        "agents/lib/batch_state.py",
        "agents/lib/task_queue.py",
        "agents/lib/final_acceptance.py",
        "agents/lib/failure_journal.py",
        "agents/lib/git_workflow.py",
        "agents/lib/multi_agent_contract.py",
    ]
    assert snapshot["controller_proof_test_paths"] == [
        "tests/test_controller_contract.py",
        "tests/test_run_task_runtime_foundations.py",
        "tests/test_task_queue.py",
    ]



def test_controller_modules_share_contract_symbols() -> None:
    contract = _load("agents.lib.controller_contract")
    batch_executor = _load("agents.lib.batch_executor")
    task_queue = _load("agents.lib.task_queue")
    batch_state = _load("agents.lib.batch_state")
    failure_journal = _load("agents.lib.failure_journal")

    assert batch_executor.ResumeMode is contract.ResumeMode
    assert task_queue.BatchPostTaskDecision is contract.BatchPostTaskDecision
    assert batch_state.BatchStatus is contract.BatchStatus
    assert failure_journal.POLICY_BLOCKED_FAILURE_CATEGORY == contract.POLICY_BLOCKED_FAILURE_CATEGORY
    assert "active_role" in contract.CHECKPOINT_TRUTH_FIELDS
    assert "controller_next_role_decision" in contract.CHECKPOINT_TRUTH_FIELDS



def test_merge_posture_and_resume_helpers_are_canonical() -> None:
    contract = _load("agents.lib.controller_contract")

    assert contract.acceptance_decision_to_terminal_status("accepted") == "completed"
    assert contract.terminal_status_to_post_task_decision("completed") == "continue"
    assert contract.merge_posture_decision_for_flow_stage("checks") == "failed_checks"
    assert contract.merge_posture_decision_for_flow_stage("reset") == "failed_reset"
    assert contract.canonical_resume_metadata(
        resume_mode="resume_after_merge",
        resume_target_task_path="tasks/001.md",
        explicit_resume=False,
    ) == {
        "resume_reason": "resume_after_merge",
        "resume_target_task_path": "tasks/001.md",
        "resume_gate": "resume_after_merge",
    }
    assert contract.checkpoint_allows_resume_after_merge(
        {
            "terminal_status": "completed",
            "acceptance_decision": "accepted",
            "post_task_decision": "continue",
            "next_task_may_proceed": True,
            "accepted_task_pr_flow_completed": True,
            "required_checks_passed": True,
            "merged_to_main": True,
            "clean_main_reset_completed": True,
        }
    ) is True
    assert contract.checkpoint_allows_resume_after_merge(
        {
            "terminal_status": "completed",
            "acceptance_decision": "accepted",
            "post_task_decision": "continue",
            "next_task_may_proceed": True,
            "accepted_task_pr_flow_completed": False,
            "required_checks_passed": True,
            "merged_to_main": True,
            "clean_main_reset_completed": True,
        }
    ) is False
    assert contract.checkpoint_requires_manual_resolution({"post_task_decision": "manual_patch"}) is True
    assert contract.checkpoint_requires_manual_resolution({"post_task_decision": "blocked"}) is True
    assert contract.resume_mode_allows_execution(
        resume_mode="resume_after_manual_resolution",
        explicit_resume=False,
    ) is False


def test_controller_failure_digest_contract_is_stable_and_machine_readable() -> None:
    contract = _load("agents.lib.controller_contract")
    repair = _load("agents.lib.controller_repair")

    snapshot = contract.controller_contract_snapshot()
    assert snapshot["controller_failure_digest_fields"] == [
        "failure_kind",
        "failure_category",
        "is_controller_failure",
        "failing_tests",
        "decision_mismatches",
        "missing_truth_fields",
        "extra_truth_fields",
        "missing_exports",
        "merge_posture_mismatches",
        "taxonomy_mismatches",
        "controller_family_files_touched",
    ]

    digest = repair.build_controller_failure_digest(
        kind="tests",
        category="tests",
        task_file="tasks/086_orchestrator_semantic_failure_digest_and_controller_repair_context.md",
        touched_files=["agents/lib/batch_executor.py", "tests/test_task_queue.py"],
        message=(
            "________________ test_controller_resume __________________\n"
            "E AssertionError: assert 'failed_merge' == 'failed_reset'\n"
            "E KeyError: 'resume_gate'\n"
            "E AttributeError: module 'agents.run_task' has no attribute 'build_controller_repair_context'\n"
            "tests/test_task_queue.py:42: AssertionError\n"
        ),
    )

    assert digest["is_controller_failure"] is True
    assert digest["failing_tests"] == ["test_controller_resume"]
    assert digest["decision_mismatches"] == [{"actual": "failed_merge", "expected": "failed_reset"}]
    assert digest["missing_truth_fields"] == ["resume_gate"]
    assert digest["missing_exports"] == ["build_controller_repair_context"]
    assert digest["merge_posture_mismatches"] == ["decision drift: actual=failed_merge expected=failed_reset"]
    assert digest["controller_family_files_touched"] == ["agents/run_task.py", "agents/lib/batch_executor.py"]


def test_resume_after_merge_requires_all_merge_reset_truth_fields() -> None:
    contract = _load("agents.lib.controller_contract")

    base = {
        "terminal_status": "completed",
        "acceptance_decision": "accepted",
        "post_task_decision": "continue",
        "next_task_may_proceed": True,
        "accepted_task_pr_flow_completed": True,
        "required_checks_passed": True,
        "merged_to_main": True,
        "clean_main_reset_completed": True,
    }
    assert contract.checkpoint_allows_resume_after_merge(base) is True

    for field_name in (
        "accepted_task_pr_flow_completed",
        "required_checks_passed",
        "merged_to_main",
        "clean_main_reset_completed",
    ):
        payload = dict(base)
        payload[field_name] = False
        assert contract.checkpoint_allows_resume_after_merge(payload) is False



def test_multi_agent_contract_snapshot_and_controller_composition_are_canonical() -> None:
    contract = _load("agents.lib.controller_contract")
    multi_agent = _load("agents.lib.multi_agent_contract")

    snapshot = multi_agent.multi_agent_contract_snapshot()
    assert snapshot["roles"] == ["controller", "builder", "verifier"]
    assert snapshot["specialist_roles"] == ["builder", "verifier"]
    assert snapshot["controller_next_role_decisions"] == [
        "controller",
        "builder",
        "verifier",
        "stop",
        "manual_patch",
        "blocked",
    ]
    assert snapshot["handoff_fields"] == [
        "active_role",
        "prior_role",
        "role_attempt_count",
        "handoff_reason",
        "handoff_summary",
        "handoff_instructions",
        "role_output_summary",
        "verifier_verdict",
        "controller_next_role_decision",
        "role_outcome",
    ]
    assert snapshot["allowed_handoffs"] == {
        "controller": ["builder", "verifier"],
        "builder": ["controller", "verifier"],
        "verifier": ["controller", "builder"],
    }
    assert snapshot["controller_authority_over_next_role"] is True
    assert snapshot["sequential_role_execution_only"] is True

    controller_snapshot = contract.controller_contract_snapshot()
    assert "active_role" in controller_snapshot["checkpoint_truth_fields"]
    assert "controller_next_role_decision" in controller_snapshot["checkpoint_truth_fields"]
    assert "agents/lib/multi_agent_contract.py" in controller_snapshot["controller_family_files"]
    assert "multi_agent_contract_snapshot" in controller_snapshot["controller_runtime_delegate_surfaces"]



def test_only_controller_may_choose_next_role() -> None:
    multi_agent = _load("agents.lib.multi_agent_contract")

    assert multi_agent.allowed_role_handoff("controller", "builder") is True
    assert multi_agent.allowed_role_handoff("builder", "verifier") is True
    assert multi_agent.allowed_role_handoff("verifier", "verifier") is False

    assert multi_agent.controller_decides_next_role(
        current_role="controller",
        proposed_next_role="builder",
        proposed_by_role="controller",
    ) == "builder"
    assert multi_agent.controller_decides_next_role(
        current_role="builder",
        proposed_next_role="verifier",
        proposed_by_role="builder",
    ) == "controller"



def test_role_handoff_truth_is_persisted_and_resume_can_reconstruct_pending_role(tmp_path: Path) -> None:
    batch_state = _load("agents.lib.batch_state")
    task_queue = _load("agents.lib.task_queue")

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
    assert state.active_role == "controller"
    assert state.controller_next_role_decision == "builder"

    state = batch_state.apply_task_result(
        state,
        task_path="tasks/001.md",
        terminal_status="completed",
        post_task_decision="continue",
        note="builder handed work to verifier",
        acceptance_decision="accepted",
        next_task_may_proceed=True,
        active_role="verifier",
        prior_role="builder",
        role_attempt_count=2,
        handoff_reason="builder_patch_ready_for_verification",
        handoff_summary="Verifier should run focused checks and summarize verdict.",
        handoff_instructions="Run focused controller proof tests first.",
        role_output_summary="Builder updated controller wrappers and persisted handoff state.",
        verifier_verdict="fail",
        controller_next_role_decision="verifier",
        role_outcome="verification_failed",
    )

    checkpoint = batch_state.last_checkpoint_for_task(state, "tasks/001.md")
    assert checkpoint is not None
    assert checkpoint.active_role == "verifier"
    assert checkpoint.prior_role == "builder"
    assert checkpoint.role_attempt_count == 2
    assert checkpoint.handoff_reason == "builder_patch_ready_for_verification"
    assert checkpoint.verifier_verdict == "fail"
    assert checkpoint.controller_next_role_decision == "verifier"

    resumed = batch_state.resume_role_handoff_state_for_batch(state, task_path="tasks/001.md")
    assert resumed["active_role"] == "verifier"
    assert resumed["pending_role"] == "verifier"
    assert resumed["controller_must_choose_next_role"] is False
