# Task 032 — Orchestrator Execution Result Normalization

## Goal

Build a normalization layer that converts raw task-runner output into a stable, structured execution result contract used by the rest of the orchestrator.

## Why

Task 031 introduced real execution. The orchestrator must now interpret output reliably across success and failure cases without each consumer parsing raw stdout/stderr independently.

## Critical compatibility requirement

This task must not break any existing passing tests.

All existing public APIs on `OrchestratorRunner` must remain backward compatible:
- `run_next_task(dry_run=False)`
- `execute_task(task)`
- `process_execution_result(execution_result, task)`
- `simulate_backlog()`

Do not change constructor signatures. Do not add required parameters to any existing method.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/execution_result.py`
- `src/builder/orchestrator/runner.py`
- `tests/test_orchestrator_execution_result.py`

All three files must be materially updated in the same bundle.

## Bundle completeness requirement

The bundle is incomplete unless all three deliverables are present.

Re-emitting an identical file is not a material update.

## Critical anti-truncation rule

`src/builder/orchestrator/runner.py` must visibly contain all of these method headers:

- `def select_next_task(`
- `def run_next_task(`
- `def execute_task(`
- `def process_execution_result(`
- `def simulate_backlog(`

And must contain a `simulate_backlog` return dict with all five keys:
- `processed_tasks`
- `stopped_reason`
- `final_status`
- `approval_required`
- `planned_actions`

A truncated `runner.py` is invalid even if the parser accepts the bundle.

## Required behavior

### Normalized result contract

`execution_result.py` must define a `normalize_execution_result(raw: dict) -> dict` function that returns:

```python
{
    "success": bool,
    "status": str,        # "success" or "failure"
    "output": str,        # combined human-readable output
    "failure_text": str,  # extracted failure reason or ""
    "changed_files": list,
    "deliverables_updated": list,
    "raw_stdout": str,
    "raw_stderr": str,
    "returncode": int,
}
```

### Normalization cases the function must handle

1. **Success case**: `returncode == 0`, extract changed files from stdout if present
2. **Lint/test failure**: `returncode != 0`, extract failure text from stderr or stdout
3. **Missing deliverables**: detect missing deliverable patterns in output
4. **Malformed output**: handle missing keys gracefully with safe defaults
5. **Unknown failure fallback**: always return a valid dict even on unexpected input

### Runner integration

`runner.py` must call `normalize_execution_result` on the raw result from `execute_task` before passing it to `process_execution_result`.

The existing legacy/mock path in `execute_task` must still return a dict that passes through `normalize_execution_result` cleanly.

## Exact legacy contract that must not be changed

These values must remain exactly the same for all existing tests:

When a pending task exists on the legacy/mock success path:
- `status == "running"`
- `message == "Task is now running."`
- `outcome == "ready_for_pr"`
- `next_action == "merge"`
- `requires_approval == False`

When review is blocked:
- `status == "running"`
- `message == "Task is now running."`
- `requires_approval == True`
- `outcome == "review_blocked"`

When no pending task:
- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`
- `outcome == "noop"`

When execution fails:
- `status == "failed"`
- `outcome == "repair_required"`
- `next_action == "require_human_review"`
- `message == "Execution failed: {failure_text}"` when failure_text is present

## CRITICAL — simulate_backlog must be implemented exactly

The test `test_orchestrator_runner_simulate_with_approval` mocks `get_next_task` using
`side_effect`. `simulate_backlog` must call `get_next_task` directly without calling
`scan_tasks()` first on each iteration.

The only valid implementation:

```python
while True:
    next_task = self.backlog_tracker.get_next_task([])
    if not next_task:
        break

    processed_tasks.append(next_task.name)
    execution_result = self.execute_task(next_task)
    result = self.process_execution_result(execution_result, next_task)

    if result["status"] == "failed":
        stopped_reason = execution_result.get("failure_text", "Execution failed")
        final_status = "failed"
        break

    if result.get("requires_approval", False):
        approval_required = True
        stopped_reason = "Approval required"
        final_status = "blocked"
        continue  # MUST be continue, NOT break

    planned_actions.append(f"Task {next_task.name} completed successfully.")
```

A solution using `select_next_task()` inside `simulate_backlog` is INVALID.
A solution using `break` when `requires_approval` is True is INVALID.

## CRITICAL — run_review behavior

When `changed_files` is empty on the legacy/mock success path:
- return `{"mergeable": True}`
- do NOT return `{"mergeable": False}`

`requires_approval` must always be derived from `run_review` result, not from whether `changed_files` is empty.

## CRITICAL — ProjectConfig must remain mutable

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.

The following must work in tests:
```python
config.task_runner_command = "python"
```

## Exact forbidden patterns

- `if not effective_changed: return {"mergeable": False}` in `run_review`
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` inside `simulate_backlog`
- calling `scan_tasks()` inside the `simulate_backlog` loop
- unused local variables like `output = execution_result.get("output", "")` that ruff will flag
- `@dataclass(frozen=True)` on any config class
- changing `status` from `"running"` to `"succeeded"` on the legacy success path

## Acceptance criteria

Tests in `tests/test_orchestrator_execution_result.py` must cover:

- success normalization
- lint/test failure normalization
- missing deliverables detection
- malformed input handling
- unknown failure fallback

All pre-existing orchestrator tests must continue to pass.

`ruff check .` must pass with no errors.
`pytest -q` must be fully green.

## Audit trail compatibility

The normalized result dict must be JSON-serializable. All fields must be primitive types (str, int, bool, list of str). This is required for audit logging in later tasks.

Do not include non-serializable objects (exceptions, file handles, etc.) in the normalized result.

## CRITICAL — process_execution_result must be implemented exactly

The agent must NOT simplify `process_execution_result`. The full implementation must be preserved, routing through `FailureClassifier`, `RepairWorkflow`, and audit log calls.

### Success path — review approved
Must return exactly:
```python
{
    "task_name": task.name,
    "status": "running",
    "message": "Task is now running.",
    "outcome": "ready_for_pr",
    "next_action": "merge",
    "requires_approval": False,
}
```

### Success path — review blocked
Must return exactly:
```python
{
    "task_name": task.name,
    "status": "running",
    "message": "Task is now running.",
    "outcome": "review_blocked",
    "next_action": "requires_approval",   # NOT "merge"
    "requires_approval": True,            # NOT False
}
```

### Failure path
Must route through `FailureClassifier` and `RepairWorkflow`. Must return:
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

Do NOT simplify the failure path to return `requires_approval: False`.
Do NOT skip `FailureClassifier` or `RepairWorkflow`.
Do NOT hardcode `next_action = "require_human_review"` without going through `repair_action`.

### Required imports in runner.py

`runner.py` must import ALL of these — do not remove any:
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

## CRITICAL — simulate_backlog with normalization

`simulate_backlog` must call `normalize_execution_result` before `process_execution_result`.
The only valid implementation:

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

## CRITICAL — stopped_reason contract

When the backlog completes normally (no failure, no approval required):
- `stopped_reason` must be `""` (empty string)
- `final_status` must be `"completed"`

Do NOT set `stopped_reason = "All tasks completed"` or any other non-empty string on clean completion.

The only times `stopped_reason` is non-empty:
- `"Execution failed"` when a task fails
- `"Approval required"` when approval is needed

## CRITICAL — normalize_execution_result integration in run_next_task

`run_next_task()` must call `normalize_execution_result` between `execute_task` and `process_execution_result`:

```python
execution_result = self.execute_task(running_task)
normalized_result = normalize_execution_result(execution_result)
return self.process_execution_result(normalized_result, running_task)
```

The default mock path in `execute_task` (no `task_runner_command`) must return:
```python
{
    "success": True,
    "output": "Task executed successfully",
    "changed_files": ["file1.py"],
}
```

This passes through `normalize_execution_result` cleanly and preserves the legacy success contract.
