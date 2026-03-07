
class RecoveryDecision:
    def __init__(self, action: str, reason: str):
        self.action = action
        self.reason = reason

def recover_from_state(current_state: str, parse_error: bool, branch_present: bool, merge_status: str) -> RecoveryDecision:
    if parse_error:
        return RecoveryDecision(action="require_human_review", reason="State file is corrupted.")
    
    if current_state == "running":
        return RecoveryDecision(action="resume", reason="Resuming previously running task.")
    
    if merge_status == "merged":
        return RecoveryDecision(action="reset_to_pending", reason="Task has already been merged.")
    
    if not branch_present:
        return RecoveryDecision(action="mark_blocked", reason="Stale branch detected.")
    
    return RecoveryDecision(action="reset_to_pending", reason="Resetting task to pending state.")
