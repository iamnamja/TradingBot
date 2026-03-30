from builder.orchestrator.ci_manager import (
    CIClassification,
    CIManager,
    CIState,
    CIStatus,
)
from builder.orchestrator.pr_manager import PRControllerState, PRManager


def test_pr_controller_native_loop_happy_path() -> None:
    pr_manager = PRManager()
    ci_manager = CIManager()

    created = pr_manager.create_or_open_pr(
        number=101,
        title="Task 059 implementation",
        branch="task/059-orchestrator-ci-pr-merge-controller",
    )
    assert created.state == PRControllerState.OPEN
    assert created.next_action == "poll_ci"
    assert created.pr is not None

    waiting = ci_manager.update_status(CIStatus(state=CIState.RUNNING))
    assert waiting.classification == CIClassification.WAIT
    assert waiting.route_to_remediation is False

    passed = ci_manager.update_status(CIStatus(state=CIState.PASSED))
    assert passed.classification == CIClassification.SAFE_TO_MERGE

    ready = pr_manager.mark_ready_to_merge()
    assert ready.state == PRControllerState.READY_TO_MERGE
    assert ready.next_action == "merge_pr"

    merged = pr_manager.mark_merged()
    assert merged.state == PRControllerState.MERGED
    assert merged.next_action == "resync_main"

    resynced = pr_manager.mark_resynced()
    assert resynced.state == PRControllerState.RESYNCED
    assert resynced.next_action == "unlock_next_task"

    unlocked = pr_manager.unlock_next_task()
    assert unlocked.state == PRControllerState.NEXT_TASK_UNLOCKED
    assert unlocked.next_action == "run_next_task"


def test_ci_failure_routes_back_to_remediation_planner() -> None:
    ci_manager = CIManager()
    decision = ci_manager.update_status(
        CIStatus(
            state=CIState.FAILED,
            provider="github",
            details="unit-tests: failed in tests/test_orchestrator_runner.py",
        )
    )
    assert decision.classification == CIClassification.REMEDIATE
    assert decision.route_to_remediation is True
    assert "failed" in decision.reason
