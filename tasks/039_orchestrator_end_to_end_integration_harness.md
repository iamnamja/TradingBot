# Task 039 — End-to-End Integration Harness

## Current baseline update

`src/builder/orchestrator/runner.py` is stable and green on `main` after Task 037.

This task is tests-only. Treat all production orchestrator code as locked baseline.

## Goal

Test the full orchestrator workflow end-to-end — from backlog discovery through execution, normalization, review gate, approval checkpoint, and PR readiness — in deterministic integration tests.

## Why

Unit tests cover individual components. This task ensures the full pipeline works correctly when all components are wired together. All external calls (subprocess, git, GitHub CLI) must be mocked so the test is fast and deterministic.

## Critical compatibility requirement

All existing public APIs must remain backward compatible. This task adds tests only — it must not change any production code signatures or behavior.

All existing passing tests must continue to pass.

## Deliverables

Create or update this exact file. It must appear in the bundle:

- `tests/test_orchestrator_end_to_end.py`

This file must be materially updated.

## CRITICAL — runner.py is PROTECTED and must NOT be included

`src/builder/orchestrator/runner.py` is a stable, fully-tested file. Do NOT include it in the bundle.
Do NOT rewrite it. Do NOT modify it. Do NOT include it as a deliverable.

If the agent believes production code changes are required, that belief is incorrect for this task.

## Bundle completeness requirement

The bundle is incomplete unless `tests/test_orchestrator_end_to_end.py` is present.

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
- mock `execute_task` or `subprocess.run` — never call a real subprocess
- mock `get_next_task` using `side_effect` for sequencing
- be deterministic and portable on Windows
- avoid relying on real repo filesystem state
- not use `BacklogTracker(tasks_directory="mock/tasks")` unless `scan_tasks` is patched or avoided
- preserve the existing `runner.py` contracts exactly

## Recommended test shape

Use real `ProjectAdapter.get_tradingbot_default_config()` objects where needed.
Prefer `MagicMock(spec=BacklogTracker)` for sequencing behavior.
Patch only the smallest seams needed:
- `backlog_tracker.get_next_task`
- `runner.execute_task`
- `runner.run_review`
- or `subprocess.run` for real-execution path coverage

Do NOT patch:
- `OrchestratorRunner.run_next_task`
- `OrchestratorRunner.process_execution_result`
- `OrchestratorRunner.simulate_backlog`

## Locked runner contracts

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
- `next_action == "require_human_review"`

## CRITICAL — simulate_backlog contract

When used in tests, it must remain behaviorally unchanged:

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

## Exact forbidden patterns

- modifying any production code
- real subprocess calls in integration tests
- relying on live git state or GitHub CLI
- relying on actual repo `tasks/` contents
- Unix-only shell commands
- unused locals or imports that ruff will flag

## Acceptance criteria

All five scenarios above have dedicated test functions.

Tests are portable on Windows.

`ruff check .` must pass. `pytest -q` must be fully green.

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.
