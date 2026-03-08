from typing import Dict, Any

def create_approval_checkpoint(task_name: str, reason: str, source: str, requested_action: str) -> Dict[str, Any]:
    return {
        "task_name": task_name,
        "reason": reason,
        "source": source,
        "requested_action": requested_action,
        "status": "pending",
        "requires_approval": True,
    }
