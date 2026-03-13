\# Task 033 — Real Review and Compliance Gate



\## Goal

Evaluate actual execution results and changed files before allowing merge readiness.



\## Why

Once execution becomes real, review must use real execution outputs.



\## Deliverables



Update:



\- `src/builder/orchestrator/runner.py`

\- `src/builder/orchestrator/review.py`

\- `src/builder/orchestrator/policy.py`

\- `tests/test\_orchestrator\_real\_review\_gate.py`



\## Required behavior



Review must determine:



\- mergeable

\- review\_blocked

\- approval\_required



Policy engine must check changed files against approval rules.



Execution result must only become `ready\_for\_pr` if:



\- execution succeeded

\- review passed

\- policy allows merge



\## Acceptance criteria



Tests cover:



\- mergeable success

\- missing deliverables

\- approval-required file changes

\- no changed files edge case


## CRITICAL — PolicyEngine exact constructor signature

`PolicyEngine.__init__` must accept exactly these parameters:

```python
class PolicyEngine:
    def __init__(
        self,
        approval_required_file_patterns: list[str],
        protected_file_patterns: list[str] | None = None,
    ) -> None:
```

The existing `test_orchestrator_policy.py` constructs it as:
```python
PolicyEngine(
    protected_file_patterns=["protected_file.py"],
    approval_required_file_patterns=["README.md", "CHANGELOG.md"]
)
```

Both keyword arguments must be accepted. Do NOT use a different parameter name such as `approval_required_patterns` or `patterns`.

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.

Correct:
```python
from builder.orchestrator.policy import PolicyEngine
from builder.orchestrator.review import ReviewChecker
```

Invalid:
```python
from src.builder.orchestrator.policy import PolicyEngine
```

## CRITICAL — process_execution_result must be implemented exactly

The agent must NOT simplify `process_execution_result`. Route through `FailureClassifier`, `RepairWorkflow`, and audit log calls.

### Review blocked path must return exactly:
```python
{
    "task_name": task.name,
    "status": "running",
    "message": "Task is now running.",
    "outcome": "review_blocked",
    "next_action": "requires_approval",   # NOT "review" or "merge"
    "requires_approval": True,
}
```

### Failure path must return:
```python
{
    "task_name": task.name,
    "status": "failed",
    "message": f"Execution failed: {failure_text}" if failure_text else "Execution failed.",
    "outcome": "repair_required",
    "next_action": next_action,           # from repair_action, fallback "require_human_review"
    "requires_approval": repair_action.get("requires_approval", True),
}
```

Do NOT return `"Task execution failed."` as the message. The format must be `"Execution failed: {text}"`.

### Required imports in runner.py
```python
from .approval import create_approval_checkpoint
from .audit import (
    log_approval_checkpoint,
    log_classification_result,
    log_repair_decision,
    log_review_verdict,
    log_selected_task,
)
from .execution_result import normalize_execution_result
from .failures import FailureClassifier
from .repair import RepairWorkflow
```

## CRITICAL — stopped_reason contract

When backlog completes normally: `stopped_reason == ""` (empty string). NEVER `"All tasks completed"`.

Only non-empty values:
- `"Execution failed"` on task failure
- `"Approval required"` when approval is needed

## CRITICAL — simulate_backlog exact implementation

```python
while True:
    next_task = self.backlog_tracker.get_next_task([])
    if not next_task:
        break

    processed_tasks.append(next_task.name)
    execution_result = self.execute_task(next_task)
    normalized_result = normalize_execution_result(execution_result)
    result = self.process_execution_result(normalized_result, next_task)

    if result["status"] == "failed":
        stopped_reason = normalized_result.get("failure_text", "Execution failed")
        final_status = "failed"
        break

    if result.get("requires_approval", False):
        approval_required = True
        stopped_reason = "Approval required"
        final_status = "blocked"
        continue  # MUST be continue, NOT break

    planned_actions.append(f"Task {next_task.name} completed successfully.")
```