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

\- `tests/test_orchestrator_real_review_gate.py`



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


## CRITICAL — process_execution_result must be implemented exactly

Do NOT simplify `process_execution_result`. Route through `FailureClassifier`, `RepairWorkflow`, and audit log calls.

### Review blocked path must return exactly:
```python
{
    "task_name": task.name,
    "status": "running",
    "message": "Task is now running.",
    "outcome": "review_blocked",
    "next_action": "requires_approval",   # NOT "review", "merge", or anything else
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
    "requires_approval": repair_action.get("requires_approval", True),  # True by default
}
```

Do NOT return `"Task execution failed."` or any other message format.
Do NOT return `requires_approval: False` on the failure path.
Do NOT skip `FailureClassifier` or `RepairWorkflow`.

### Required imports in runner.py — do not remove any:
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

When backlog completes normally: `stopped_reason == ""` (empty string). NEVER `"All tasks completed"` or any other non-empty value.

Only non-empty values allowed:
- `"Execution failed"` on task failure
- `"Approval required"` when approval is needed

## CRITICAL — simulate_backlog with normalization

Must call `normalize_execution_result` before `process_execution_result`:

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

## CRITICAL — run_next_task normalization

Must call `normalize_execution_result` between `execute_task` and `process_execution_result`:

```python
execution_result = self.execute_task(running_task)
normalized_result = normalize_execution_result(execution_result)
return self.process_execution_result(normalized_result, running_task)
```

## CRITICAL — execute_task default mock return

When `task_runner_command` is None, return exactly:
```python
{
    "success": True,
    "output": "Task executed successfully",
    "changed_files": ["file1.py"],
}
```

Do NOT return `{"success": True, "changed_files": []}` — the empty list causes test failures.

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.

Correct:
```python
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.policy import PolicyEngine
```

Invalid (breaks CI):
```python
from src.builder.orchestrator.runner import OrchestratorRunner
```

## CRITICAL — PolicyEngine exact constructor signature

`PolicyEngine.__init__` must accept exactly these keyword arguments:

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

Both keyword arguments must be accepted. Do NOT use `approval_required_patterns` or any other name.
