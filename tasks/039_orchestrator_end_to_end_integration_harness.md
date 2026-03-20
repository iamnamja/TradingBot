# Task 039 — End-to-End Integration Harness

## Goal

Add deterministic integration tests for the orchestrator workflow using the current stable `runner.py` and CLI baselines from Tasks 037–038c.

## Why

Task 039 remains tests-only. CLI wiring and decision logging were already completed in Tasks 038b/038c, so this task should validate the current runner workflow without inviting production rewrites.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_orchestrator_end_to_end.py`

The listed file must be materially updated.

## Harness policy

- FILE: src/builder/orchestrator/runner.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/cli.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

This task adds tests only. It must not change any production code signatures or behavior.

All existing passing tests must continue to pass.

## Current implementation surface to target

Write tests against the current `main` runner surface exactly as it exists today:

- `OrchestratorRunner.__init__(config, backlog_tracker, initial_state)`
- `run_next_task(dry_run=False)`
- `run_loop(max_tasks=100)`
- `simulate_backlog()`

Do **not** invent or assume any of the following unless they already exist on `main`:

- `runner.run()`
- zero-argument `OrchestratorRunner()`
- alternate constructor keyword names
- `BacklogTask` imports if the module does not export that symbol
- different `run_loop()` return shapes than the current implementation

## Required integration scenarios

### Scenario 1 — Full success path

- use `runner.run_loop()`
- backlog has two pending tasks
- both execute successfully
- review passes for both
- both reach `outcome == "ready_for_pr"`
- `processed_tasks == ["001_task.py", "002_task.py"]`
- `final_status == "completed"`

### Scenario 2 — Execution failure stops the loop

- use `runner.run_loop()`
- backlog has two pending tasks
- first task fails execution
- loop stops after first task
- `processed_tasks == ["001_task.py"]`
- `final_status == "failed"`

### Scenario 3 — Approval checkpoint

- use `runner.run_loop()`
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
- `run_next_task(dry_run=True)` returns `status == "planned"`

## Test-shaping rules

All tests must:

- preserve the current `OrchestratorRunner` constructor contract
- avoid real subprocesses
- be deterministic and portable on Windows
- avoid relying on actual repo filesystem state
- avoid relying on actual repo `tasks/` contents
- not patch `OrchestratorRunner.process_execution_result`
- not modify production code contracts via tests

## Required mocking guidance

Because the real runner currently reads backlog state from the tracker/config surface, tests must use one of these safe patterns:

1. provide a minimal config stub that includes at least `tasks_directory` or `state_path`, and a backlog tracker stub that supports the methods the runner will call, including any of:
   - `scan_tasks()`
   - `load_state()`
   - `save_state()`
   - `get_next_task(tasks)`

or

2. patch higher-level runner methods such as `read_backlog()` and `select_next_task()` while preserving the public constructor shape.

Tests must not assume a simpler runner surface than the one currently on `main`.

## Assertion guidance

Prefer asserting the existing public return keys that actually exist today, such as:

- `task_name`
- `status`
- `message`
- `outcome`
- `next_action`
- `requires_approval`
- `processed_tasks`
- `stopped_reason`
- `final_status`
- `approval_required`
- `planned_actions`

Do not assert fields that do not exist on the current public contract.

## Exact forbidden patterns

- modifying any production code
- including `runner.py` in the bundle
- including `cli.py` in the bundle
- real subprocess calls
- relying on live git state or GitHub CLI
- relying on actual repo `tasks/` contents
- calling `runner.run()`
- constructing `OrchestratorRunner()` without the required arguments
- importing symbols from `builder.orchestrator.backlog` that are not present on `main`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- the integration harness validates the real orchestrator flow without production edits

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.
