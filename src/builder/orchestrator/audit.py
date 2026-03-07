import json
from datetime import datetime
from typing import Dict, Any

def log_event(event: str, payload: Dict[str, Any], audit_path: str) -> None:
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_entry = {
        "event": event,
        "timestamp": timestamp,
        **payload
    }
    with open(audit_path, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")

def log_selected_task(task_name: str, audit_path: str) -> None:
    log_event("selected_task", {"task_name": task_name}, audit_path)

def log_classification_result(result: str, audit_path: str) -> None:
    log_event("classification_result", {"result": result}, audit_path)

def log_review_verdict(verdict: str, audit_path: str) -> None:
    log_event("review_verdict", {"verdict": verdict}, audit_path)

def log_pr_action(action: str, audit_path: str) -> None:
    log_event("pr_action", {"action": action}, audit_path)

def log_merge_decision(decision: str, audit_path: str) -> None:
    log_event("merge_decision", {"decision": decision}, audit_path)

def log_repair_decision(decision: str, audit_path: str) -> None:
    log_event("repair_decision", {"decision": decision}, audit_path)

def log_stop_escalation_decision(decision: str, audit_path: str) -> None:
    log_event("stop_escalation_decision", {"decision": decision}, audit_path)
