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

## CRITICAL — run_review must use PolicyEngine

`run_review` must wire `PolicyEngine` to check `approval_required_file_patterns` from config:

```python
def run_review(self, changed_files: list[str]) -> dict[str, Any]:
    effective_changed = list(changed_files or [])

    if not effective_changed:
        return {"mergeable": True}

    # Check policy — approval_required_file_patterns blocks merge
    approval_patterns = getattr(
        self.config, "approval_required_file_patterns", []
    )
    policy = PolicyEngine(
        approval_required_file_patterns=approval_patterns,
        protected_file_patterns=getattr(self.config, "protected_file_patterns", []),
    )
    if policy.requires_approval(effective_changed):
        return {"mergeable": False}

    checker = ReviewChecker(
        deliverables=effective_changed,
        changed_files=effective_changed,
    )
    result = checker.evaluate()
    if "mergeable" not in result:
        return {"mergeable": True}
    return result
```

This means:
- `changed_files=[]` → `{"mergeable": True}` (legacy mock path preserved)
- `changed_files=["README.md"]` with `approval_required_file_patterns=["README.md"]` → `{"mergeable": False}` → `review_blocked`
- `changed_files=["file1.py"]` with no matching patterns → `{"mergeable": True}` → `ready_for_pr`

## CRITICAL — execute_task default mock return must use empty changed_files

`test_execute_task_without_real_command` expects `result["changed_files"] == []`.

When `task_runner_command` is None, return exactly:
```python
{
    "success": True,
    "output": "Task executed successfully",
    "changed_files": [],
}
```

Do NOT return `"changed_files": ["file1.py"]` — this breaks the test.

The legacy tests that need `ready_for_pr` on the mock path work because `run_review([])` returns `{"mergeable": True}`.

## CRITICAL — next_action must be "merge" not "create_pr"

Tests expect `next_action == "merge"` on the ready_for_pr path. Do NOT change this to `"create_pr"`.

The ready_for_pr return must be exactly:
```python
{
    "task_name": task.name,
    "status": "running",
    "message": "Task is now running.",
    "outcome": "ready_for_pr",
    "next_action": "merge",          # NOT "create_pr"
    "requires_approval": False,
}
```

## CRITICAL — PolicyEngine.requires_approval signature

`PolicyEngine` must have a `requires_approval(changed_files: list[str]) -> bool` method:

```python
def requires_approval(self, changed_files: list[str]) -> bool:
    """Returns True if any changed file matches any approval-required pattern."""
    for pattern in self.approval_required_file_patterns:
        for f in changed_files:
            if pattern in f or f.endswith(pattern):
                return True
    return False
```

## CRITICAL — test_missing_deliverables behavior

`test_missing_deliverables` passes `changed_files=["other_file.py"]` and `deliverables_updated=[]` and expects `outcome == "review_blocked"`.

This means `ReviewChecker` must return `{"mergeable": False}` when `deliverables_updated` is empty but `changed_files` is non-empty. Update `ReviewChecker.evaluate()` to check this:

```python
def evaluate(self) -> dict[str, Any]:
    # If deliverables list is provided but empty, block merge
    if hasattr(self, 'deliverables') and self.deliverables is not None:
        if len(self.deliverables) == 0 and len(self.changed_files) > 0:
            return {"mergeable": False, "reason": "no_deliverables_updated"}
    ...
```

Or alternatively: pass `deliverables_updated` from the normalized result into `ReviewChecker` so it can check whether deliverables were actually updated.
