# Task 039 — End-to-End Integration Harness

## Goal

Add deterministic integration tests for the current stable orchestrator workflow using the real `runner.py` baseline now on `main`.

## Why

Task 039 is tests-only. The current failures are caused by tests inventing symbols and APIs that do not exist on the current baseline.

This task must validate the real current runner surface without changing production code.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_orchestrator_end_to_end.py`

The listed file must be materially updated.

## Harness policy

- FILE: src/builder/orchestrator/runner.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/cli.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/backlog.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/execution_result.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

This task adds tests only. It must not change any production code signatures or behavior.

All existing passing tests must continue to pass.

## Current runner baseline — must match exactly

The tests must target the current real baseline on `main`:

- `OrchestratorRunner.__init__(config, backlog_tracker, initial_state)`
- `run_next_task(dry_run=False)`
- `run_loop(max_tasks=100)`

`run_loop()` currently calls `run_next_task()` internally and returns:

```python
{
    "processed_tasks": list[str],
    "stopped_reason": str,
    "final_status": str,
    "approval_required": bool,
    "planned_actions": list[str],
}
```

`run_next_task()` currently returns dicts like:

- no task:
  - `task_name == "none"`
  - `status == "no_task"`
- dry run:
  - `status == "planned"`
- failure:
  - `status == "failed"`
- blocked review:
  - `status == "running"`
  - `requires_approval == True`
- success:
  - `status == "running"`
  - `outcome == "ready_for_pr"`

## Required test construction rules

Build the runner using the real constructor surface.

Use a small real config-like object shape and a stub backlog tracker object. Do not instantiate `OrchestratorRunner()` with zero arguments.

The test harness should use:
- a config object with at least:
  - `tasks_directory`
  - `state_path`
  - `approval_required_file_patterns`
  - `protected_file_patterns`
  - `task_runner_command`
  - `audit_path`
- a stub backlog tracker with methods:
  - `scan_tasks()`
  - `load_state(path)`
  - `save_state(path, tasks)`
  - `get_next_task(tasks)`

Use `OrchestratorState(tasks=[])` for `initial_state`.

Use lightweight stub task objects that expose:
- `name`
- `order`
- `status`

Do not rely on undocumented backlog types.

## Required integration scenarios

### Scenario 1 — Full success path

Use the real `run_loop()` and patch `runner.run_next_task` to return:

1. first task success result
2. second task success result
3. final no-task sentinel

Assert:
- `processed_tasks == ["001_task.py", "002_task.py"]`
- `final_status == "completed"`
- `approval_required is False`

### Scenario 2 — Execution failure stops the loop

Use the real `run_loop()` and patch `runner.run_next_task` to return:

1. first task failed result

Assert:
- `processed_tasks == ["001_task.py"]`
- `final_status == "failed"`

### Scenario 3 — Approval checkpoint blocks run

Use the real `run_loop()` and patch `runner.run_next_task` to return:

1. first task success result
2. second task blocked-for-approval result

Assert:
- `processed_tasks == ["001_task.py", "002_task.py"]`
- `approval_required is True`
- `final_status == "blocked"`

### Scenario 4 — Empty backlog

Construct the real runner and patch only the backlog/state read path as needed so `run_next_task()` sees no pending task.

Assert:
- `run_next_task()["status"] == "no_task"`

### Scenario 5 — Dry run

Construct the real runner and patch only the backlog/state read path as needed so `run_next_task(dry_run=True)` sees one pending task without executing it.

Assert:
- `status == "planned"`

## Test rules

All tests must:

- be deterministic and portable on Windows
- avoid real subprocess calls
- avoid relying on real repo `tasks/` contents
- avoid relying on live git state or GitHub CLI
- not modify production code contracts via tests

For `run_loop()` scenarios, prefer patching `runner.run_next_task` directly because that is the current engine contract from Task 038a.

For `run_next_task()` scenarios, patch only the minimal backlog/state behavior needed to exercise the real method.

## Exact forbidden patterns

- modifying any production code
- including `runner.py` in the bundle
- including `cli.py` in the bundle
- including `backlog.py` in the bundle
- including `execution_result.py` in the bundle
- real subprocess calls
- relying on live git state or GitHub CLI
- relying on actual repo `tasks/` contents
- zero-argument `OrchestratorRunner()`
- calling nonexistent methods like `runner.run()` or `runner.run_all_tasks()`
- importing nonexistent symbols such as:
  - `BacklogTask`
  - `BacklogItem`
  - `BacklogStore`
  - `TaskRecord`
  - `TaskState`
  - `ExecutionResult`

## CRITICAL — valid import surface

Allowed imports for this test file should be limited to real current symbols such as:

- `from builder.orchestrator.runner import OrchestratorRunner`
- `from builder.orchestrator.state import OrchestratorState`

Only import additional symbols if they are confirmed to exist on the current baseline.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- the integration harness validates the real current orchestrator flow without production edits
