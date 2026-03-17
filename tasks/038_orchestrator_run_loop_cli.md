# Task 038 — Run Loop CLI

## Goal

Add a CLI run loop that processes tasks continuously until the backlog is complete, a failure occurs, or approval is required.

## Why

Currently the orchestrator processes one task at a time via `run_next_task()`. A run loop automates backlog processing end-to-end without manual re-invocation for each task.

## Critical compatibility requirement

All existing public APIs must remain backward compatible:
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged — do NOT add mode parameters
- `simulate_backlog()` signature and return contract unchanged

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_run_loop_cli.py`

All three files must be materially updated in the same bundle.


## CRITICAL — runner.py surgical update ONLY

`src/builder/orchestrator/runner.py` is included as a deliverable ONLY to add the `run_loop()` method.

The agent must:
- Copy the ENTIRE existing runner.py exactly as-is
- Add ONLY the `run_loop()` method at the end of the class, before `simulate_backlog()`
- Change NOTHING else — no existing methods, no imports, no class structure

Any change to existing methods (run_next_task, execute_task, process_execution_result, simulate_backlog, run_review, etc.) is INVALID and will cause test failures.

The existing runner.py passes all tests. Only `run_loop()` is new.

## Bundle completeness requirement

The bundle is incomplete unless all three deliverables are present.

## Critical anti-truncation rule

`src/builder/orchestrator/runner.py` must visibly contain all of these method headers:

- `def select_next_task(`
- `def run_next_task(`
- `def execute_task(`
- `def process_execution_result(`
- `def simulate_backlog(`

And must contain a `simulate_backlog` return dict with all five keys:
`processed_tasks`, `stopped_reason`, `final_status`, `approval_required`, `planned_actions`

## Required behavior

### CLI modes

`cli.py` must support four modes via subcommand or flag:

```
run-once     — run a single task (existing behavior)
run-loop     — run tasks continuously until stop condition
simulate     — run simulation without real execution
resume       — resume from approval checkpoint
```

### run-loop behavior

The run loop must stop when any of:
- no more pending tasks (backlog complete)
- a task fails
- approval is required

On each iteration the loop must:
1. Call `run_next_task()`
2. Print task name and outcome
3. Check stop condition
4. Continue or stop

### CLI output format

Each iteration must print:
```
[Task N] task_name — outcome (next_action)
```

Final summary must print:
```
Run complete: {final_status}
Tasks processed: {count}
Stopped reason: {reason}
```

### runner.py

Must add `run_loop()` method:

```python
def run_loop(self, max_tasks: int = 100) -> dict[str, Any]:
    """
    Run tasks continuously until stop condition.
    Returns summary dict with processed_tasks, final_status, stopped_reason.
    """
```

`run_loop` must call `run_next_task()` internally — do not duplicate execution logic.

## Exact legacy contract that must not be changed

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

When no pending task:
- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`

When execution fails:
- `status == "failed"`
- `outcome == "repair_required"`

## CRITICAL — simulate_backlog must be implemented exactly

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

## CRITICAL — run_review behavior

When `changed_files` is empty on the legacy/mock success path, return `{"mergeable": True}`.

## CRITICAL — ProjectConfig must remain mutable

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.

## Exact forbidden patterns

- adding required parameters to `run_next_task`
- duplicating execution logic in `run_loop` instead of calling `run_next_task`
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop
- `@dataclass(frozen=True)` on any config class
- unused local variables that ruff will flag

## Acceptance criteria

Tests in `tests/test_orchestrator_run_loop_cli.py` must cover:

- run-loop stops when backlog is complete
- run-loop stops on task failure
- run-loop stops when approval is required
- simulate mode runs without real execution
- max_tasks guard prevents infinite loops

`ruff check .` must pass. `pytest -q` must be fully green.

## Decision logging

The run loop must write a structured decision log entry after each task. At minimum:

```python
{
    "task_name": str,
    "outcome": str,
    "timestamp": str,  # ISO format
    "iteration": int,
}
```

Log entries must be appended to `getattr(self.config, "audit_path", None)` if configured, otherwise skip logging silently.

Do not raise errors if audit_path is not configured.

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
