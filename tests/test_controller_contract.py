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
            "acceptance_decision": "accepted",
            "post_task_decision": "continue",
            "next_task_may_proceed": True,
            "merged_to_main": True,
            "clean_main_reset_completed": True,
        }
    ) is True
