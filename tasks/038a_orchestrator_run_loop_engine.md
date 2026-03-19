# Task 038a — Run Loop Engine

## Goal

Add a single `run_loop()` engine method to `OrchestratorRunner` without changing any existing `runner.py` behavior.

## Why

Task 038 previously failed because the agent rewrote existing `runner.py` methods. This subtask isolates the risky production change to one additive method plus focused tests.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/runner.py`
- `tests/test_orchestrator_run_loop_engine.py`

Both files must be materially updated in the same bundle.

## Harness policy

- FILE: src/builder/orchestrator/runner.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=run_loop ANCHOR_BEFORE=simulate_backlog MAX_CHANGED_LINES=160
- FILE: src/builder/orchestrator/cli.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

All existing public APIs must remain backward compatible:

- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged
- `simulate_backlog()` signature and return contract unchanged
- existing return dict keys and message strings unchanged

All existing passing tests must continue to pass.

## Required behavior

Add only this method:

```python
def run_loop(self, max_tasks: int = 100) -> dict[str, Any]:
    """
    Run tasks continuously until stop condition.
    Returns summary dict with processed_tasks, final_status, stopped_reason,
    approval_required, planned_actions.
    """
```

`run_loop()` must call `run_next_task()` internally.

## Stop conditions

Stop when any of:

- no pending task is available
- a task fails
- approval is required
- `max_tasks` is reached

## Summary contract

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

Use `final_status == "completed"` when the backlog empties normally.

Do not count the final no-task sentinel iteration as a processed task.

## Locked runner contracts

Do NOT change any of the following existing behaviors:

### legacy/mock success path

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
- `next_action == "requires_approval"`

### no pending task

- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`
- `outcome == "noop"`
- `next_action == "none"`

### execution failure

- `status == "failed"`
- `outcome == "repair_required"`
- `next_action == "require_human_review"`
- `requires_approval == True`
- `message == "Execution failed: {text}"` when `failure_text` or `stderr` exists

## Exact forbidden patterns

- modifying any existing `runner.py` method other than adding `run_loop()`
- changing imports in `runner.py`
- changing any status/outcome/message string
- duplicating execution logic instead of calling `run_next_task()`
- editing `simulate_backlog()`
- editing `process_execution_result()`
- editing `execute_task()`
- editing `run_review()`
- adding CLI behavior in this task

## Test requirements

`tests/test_orchestrator_run_loop_engine.py` must cover:

- run loop stops when backlog completes
- run loop stops on failure
- run loop stops on approval required
- `max_tasks` stops infinite looping
- no-task sentinel is not counted
- normal completion uses `final_status == "completed"`

Tests must be deterministic, portable on Windows, and not rely on the real repo `tasks/` directory.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `runner.py` changes are limited to one additive method
- all existing runner tests remain green
- new engine tests are green

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.
