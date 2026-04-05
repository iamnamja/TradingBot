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
