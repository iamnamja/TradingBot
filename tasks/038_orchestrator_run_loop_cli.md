# Task 038 — Run Loop CLI

## Current baseline update

`src/builder/orchestrator/runner.py` is now stable and green on `main` after Task 037.

For this task, treat the current `runner.py` on `main` as the locked baseline.

### Updated deliverable guidance

Primary work should be in:
- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_run_loop_cli.py`

`src/builder/orchestrator/runner.py` is included only because this task needs one small additive method:
- `run_loop(...)`

A solution is invalid if it materially rewrites or regresses the current green `runner.py`.

### Additional explicit instruction

Before editing anything, first read the current `main` versions of:
- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/cli.py`

Then preserve the current `runner.py` implementation exactly and add only the new method described below.

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
- copy the ENTIRE existing `runner.py` exactly as-is
- add ONLY the `run_loop()` method
- change NOTHING else — no existing methods, no imports, no class structure, no return contracts

Any change to existing methods (`run_next_task`, `execute_task`, `process_execution_result`, `simulate_backlog`, `run_review`, etc.) is INVALID and will cause test failures.

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
- `max_tasks` is reached

On each iteration the loop must:
1. Call `run_next_task()`
2. Print task name and outcome
3. Write a decision log entry if `audit_path` is configured
4. Check stop condition
5. Continue or stop

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

Must add this method only:

```python
def run_loop(self, max_tasks: int = 100) -> dict[str, Any]:
    """
    Run tasks continuously until stop condition.
    Returns summary dict with processed_tasks, final_status, stopped_reason,
    approval_required, planned_actions.
    """
```

`run_loop()` must call `run_next_task()` internally — do not duplicate execution logic.

A valid return shape is:

```python
{
    "processed_tasks": list[str],
    "stopped_reason": str,
    "final_status": str,
    "approval_required": bool,
    "planned_actions": list[str],
}
```

### decision logging

The run loop must write a structured decision log entry after each task. At minimum:

```python
{
    "task_name": str,
    "outcome": str,
    "timestamp": str,  # ISO format
    "iteration": int,
}
```

Append to `getattr(self.config, "audit_path", None)` if configured, otherwise skip silently.

Do not raise if `audit_path` is missing.

## Locked runner contracts

Do NOT change any of the following existing behaviors:

### pending task on legacy/mock success path
- `status == "running"`
- `message == "Task is now running."`
- `outcome == "ready_for_pr"`
- `next_action == "merge"`
- `requires_approval == False`

### review blocked
- `status == "running"`
- `message == "Task is now running."`
- `requires_approval == True`
- `outcome == "review_blocked"`

### no pending task
- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`

### execution failure
- `status == "failed"`
- `outcome == "repair_required"`

## CRITICAL — simulate_backlog must remain unchanged

Do not modify `simulate_backlog()`.

It must continue to behave exactly like:

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
        continue

    planned_actions.append(f"Task {next_task.name} completed successfully.")
```

## CRITICAL — run_review behavior

When `changed_files` is empty on the legacy/mock success path, return `{"mergeable": True}`.

## Exact forbidden patterns

- modifying any existing `runner.py` method other than adding `run_loop()`
- adding required parameters to `run_next_task`
- duplicating execution logic in `run_loop` instead of calling `run_next_task`
- editing `execute_task()` default mock return
- editing `process_execution_result()`
- editing `simulate_backlog()`
- editing guardrail semantics
- Unix-only CLI logic that breaks on Windows
- unused locals or imports that ruff will flag

## Acceptance criteria

Tests in `tests/test_orchestrator_run_loop_cli.py` must cover:

- run-loop stops when backlog is complete
- run-loop stops on task failure
- run-loop stops when approval is required
- simulate mode runs without real execution
- max_tasks guard prevents infinite loops
- run-loop writes decision logs when `audit_path` is configured
- run-loop does not fail when `audit_path` is not configured

`ruff check .` must pass. `pytest -q` must be fully green.

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.
