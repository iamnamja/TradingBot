# Task 042d — Thin `run_task.py` Shell and Parity

## Goal

Validate that `agents/run_task.py` now behaves as a thin orchestration shell over the extracted modules, while preserving current behavior exactly.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_run_task_shell_parity.py`

The listed file must be materially updated.

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

This task must not introduce new product behavior.

This is a **tests-only parity validation task**. By the time 042d runs, the extraction work should already be complete from 042a / 042b / 042c.

The thin shell must preserve the current public workflow:

- task loading
- message construction
- provider execution delegation
- parser/policy delegation
- semantic preflight delegation
- retry loop
- local check execution
- commit/push flow
- task-state integration

## Test requirements

Add deterministic tests that prove the shell still orchestrates the same flow, including:

1. provider call path still runs through the extracted provider module
2. parser/policy modules are actually used
3. semantic preflight module is actually used
4. known runtime artifact handling still appears in warnings/flow
5. external behavior on green and failing paths is unchanged

## Exact forbidden patterns

- new feature work
- behavior changes to retry counts, branch naming, or approval behavior
- moving product logic into tests instead of the extracted modules
- touching orchestrator engine files under `src/builder/orchestrator/`
- touching `agents/run_task.py`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `run_task.py` is validated as a thin shell relative to the prior monolith
- no public behavior changes are introduced
