from builder.orchestrator.backlog_state import BacklogStatus
from builder.orchestrator.orchestrator_runtime import OrchestratorRuntimeState


def test_runtime_resumes_and_selects_ready_after_approval_wait():
    runtime = OrchestratorRuntimeState()
    runtime.register_task("001", status=BacklogStatus.COMPLETED)
    runtime.register_task("002", status=BacklogStatus.WAITING_APPROVAL)
    runtime.register_task("003", status=BacklogStatus.READY)

    first_pick = runtime.pick_next_ready_task(["001", "002", "003"])
    assert first_pick == "003"

    runtime.set_task_status("002", BacklogStatus.READY, approval_ref="approved")
    second_pick = runtime.pick_next_ready_task(["001", "002", "003"])
    assert second_pick == "002"


def test_runtime_persists_backlog_and_context_for_resume():
    runtime = OrchestratorRuntimeState()
    runtime.register_task("010", status=BacklogStatus.BLOCKED)
    runtime.set_task_status("010", BacklogStatus.BLOCKED, reason="needs schema migration")
    runtime.register_task("011", status=BacklogStatus.MANUAL_PATCH)
    runtime.set_task_status(
        "011",
        BacklogStatus.MANUAL_PATCH,
        manual_patch_note="apply vendor diff",
    )
    runtime.remember_remediation_context(last_failure="lint", lane="repair")
    runtime.remember_autonomy_context(loop_iteration="4", mode="continuous")

    payload = runtime.to_dict()
    restored = OrchestratorRuntimeState.from_dict(payload)

    assert restored.backlog_state.get("010").status == BacklogStatus.BLOCKED
    assert restored.backlog_state.get("010").blocker_reason == "needs schema migration"
    assert restored.backlog_state.get("011").status == BacklogStatus.MANUAL_PATCH
    assert restored.backlog_state.get("011").manual_patch_note == "apply vendor diff"
    assert restored.remediation_context["lane"] == "repair"
    assert restored.autonomy_context["mode"] == "continuous"
