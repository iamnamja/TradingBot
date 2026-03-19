# Task 039 — End-to-End Integration Harness

## Goal

Add deterministic integration tests for the orchestrator workflow using the current stable `runner.py` and CLI baselines from Tasks 037–038c.

## Why

Task 039 is now tests-only. CLI wiring and decision logging were split into Task 038b/038c so this task can validate the flow without inviting production rewrites.

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

## Required integration scenarios

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

## Test rules

All tests must:

- mock `execute_task`, `run_review`, `get_next_task`, or `subprocess.run` as appropriate
- never call a real subprocess
- be deterministic and portable on Windows
- avoid relying on actual repo filesystem state
- not patch `OrchestratorRunner.process_execution_result`
- not modify production code contracts via tests

## Exact forbidden patterns

- modifying any production code
- including `runner.py` in the bundle
- including `cli.py` in the bundle
- real subprocess calls
- relying on live git state or GitHub CLI
- relying on actual repo `tasks/` contents

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- the integration harness validates the real orchestrator flow without production edits

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.
