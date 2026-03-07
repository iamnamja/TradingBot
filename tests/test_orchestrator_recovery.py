from builder.orchestrator.recovery import recover_from_state

def test_recover_from_running_state():
    decision = recover_from_state("running", False, True, "not_merged")
    assert decision.action == "resume"
    assert decision.reason == "Resuming previously running task."

def test_recover_from_parse_error():
    decision = recover_from_state("unknown", True, True, "not_merged")
    assert decision.action == "require_human_review"
    assert decision.reason == "State file is corrupted."

def test_recover_from_merged_task():
    decision = recover_from_state("completed", False, True, "merged")
    assert decision.action == "reset_to_pending"
    assert decision.reason == "Task has already been merged."

def test_recover_from_stale_branch():
    decision = recover_from_state("pending", False, False, "not_merged")
    assert decision.action == "mark_blocked"
    assert decision.reason == "Stale branch detected."

def test_recover_to_pending():
    decision = recover_from_state("pending", False, True, "not_merged")
    assert decision.action == "reset_to_pending"
    assert decision.reason == "Resetting task to pending state."
