from __future__ import annotations

from builder.orchestrator.backlog_state import BacklogStatus
from builder.orchestrator.ci_manager import CIState, CIStatus
from builder.orchestrator.orchestrator_runtime import (
    OrchestratorAutonomyLoop,
    TaskExecutionOutcome,
    TaskExecutionRequest,
)


def test_orchestrator_autonomy_loop_recovers_and_advances_backlog() -> None:
    loop = OrchestratorAutonomyLoop()
    ordered = ["task_impl_001", "task_docs_002"]

    for task_id in ordered:
        loop.runtime_state.register_task(task_id, status=BacklogStatus.READY)

    attempts: dict[str, int] = {}
    repaired: list[str] = []

    def execute_task(request: TaskExecutionRequest) -> TaskExecutionOutcome:
        attempts[request.task_id] = attempts.get(request.task_id, 0) + 1
        if request.task_id == "task_impl_001" and attempts[request.task_id] == 1:
            return TaskExecutionOutcome(
                success=False,
                runner_output="runtime artifact committed",
                failure_text="runtime artifact committed",
                changed_files=["logs/tmp.cache"],
            )
        return TaskExecutionOutcome(
            success=True,
            runner_output="ok",
            failure_text="",
            changed_files=[request.task_id + ".py"],
        )

    def run_localized_repair(task_id: str, action: str) -> bool:
        repaired.append(f"{task_id}:{action}")
        return action == "clean_repo"

    def ci_provider(_: str) -> CIStatus:
        return CIStatus(state=CIState.PASSED, provider="local", details="all green")

    result_one = loop.run_iteration(
        ordered,
        execute_task=execute_task,
        run_localized_repair=run_localized_repair,
        ci_provider=ci_provider,
    )
    result_two = loop.run_iteration(
        ordered,
        execute_task=execute_task,
        run_localized_repair=run_localized_repair,
        ci_provider=ci_provider,
    )

    assert result_one["status"] == "completed"
    assert result_two["status"] == "completed"
    assert attempts["task_impl_001"] == 2
    assert repaired == ["task_impl_001:clean_repo"]
    assert loop.runtime_state.backlog_state.get("task_impl_001").status == BacklogStatus.COMPLETED
    assert loop.runtime_state.backlog_state.get("task_docs_002").status == BacklogStatus.COMPLETED
