# Task 039 — End-to-End Integration Harness

## Goal

Test the full orchestrator workflow end-to-end — from backlog discovery through execution, normalization, review gate, approval checkpoint, and PR readiness — in a single deterministic integration test.

## Why

Unit tests cover individual components. This task ensures the full pipeline works correctly when all components are wired together. All external calls (subprocess, git, GitHub CLI) must be mocked so the test is fast and deterministic.

## Critical compatibility requirement

All existing public APIs must remain backward compatible. This task adds tests only — it must not change any production code signatures.

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_orchestrator_end_to_end.py`
- `src/builder/orchestrator/runner.py`

Both files must be materially updated in the same bundle.

`runner.py` may only be updated if a genuine bug is found during integration testing. If no bugs are found, it must still be included in the bundle with at least a meaningful docstring or comment update. Re-emitting identical content without any change is not acceptable.

## Bundle completeness requirement

The bundle is incomplete unless both deliverables are present.

## Critical anti-truncation rule

`src/builder/orchestrator/runner.py` must visibly contain all of these method headers:

- `def select_next_task(`
- `def run_next_task(`
- `def execute_task(`
- `def process_execution_result(`
- `def simulate_backlog(`

And must contain a `simulate_backlog` return dict with all five keys:
`processed_tasks`, `stopped_reason`, `final_status`, `approval_required`, `planned_actions`

## Required integration test coverage

`tests/test_orchestrator_end_to_end.py` must contain at least these scenarios:

### Scenario 1 — Full success path
- backlog has two pending tasks
- both execute successfully
- review passes for both
- both reach `outcome == "ready_for_pr"`
- `processed_tasks == ["001_task.py", "002_task.py"]`

### Scenario 2 — Execution failure stops the loop
- backlog has two pending tasks
- first task fails execution
- loop stops after first task
- `final_status == "failed"`

### Scenario 3 — Approval checkpoint
- backlog has two pending tasks
- first task succeeds
- second task triggers approval requirement
- `processed_tasks == ["001_task.py", "002_task.py"]`
- `approval_required == True`
- `final_status == "blocked"`

### Scenario 4 — Empty backlog
- no pending tasks
- `run_next_task()` returns `status == "no_task"`

### Scenario 5 — Dry run
- dry run does not execute any task
- returns `status == "planned"`

## Test implementation rules

All tests must:
- mock `execute_task` or `subprocess.run` — never call real subprocess in integration tests
- mock `get_next_task` using `side_effect` for sequencing
- be deterministic and portable on Windows
- not rely on filesystem state (no real `tasks/` directory required)
- not use `BacklogTracker(tasks_directory="mock/tasks")` without patching `scan_tasks`

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
- `outcome == "review_blocked"`

When no pending task:
- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`

When execution fails:
- `status == "failed"`
- `outcome == "repair_required"`
- `next_action == "require_human_review"`

## CRITICAL — simulate_backlog must be implemented exactly

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

## CRITICAL — run_review behavior

When `changed_files` is empty on the legacy/mock success path, return `{"mergeable": True}`.

## CRITICAL — ProjectConfig must remain mutable

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.

## Exact forbidden patterns

- real subprocess calls in integration tests
- relying on filesystem for task discovery without mocking
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop
- `@dataclass(frozen=True)` on any config class
- unused local variables that ruff will flag
- using `plain echo` as subprocess command

## Acceptance criteria

All five scenarios above have dedicated test functions.

Tests are portable on Windows (no Unix-only shell commands).

`ruff check .` must pass. `pytest -q` must be fully green.
