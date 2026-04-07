# Task 120 — Orchestrator repair planner ranking and rollback to last green

## Why this task exists

The orchestrator can already suppress repeated no-progress repairs, but it still lacks a stronger planner for choosing among repair options and recovering from a repair that made the repo worse.

## Outcome

Add repair-plan ranking and bounded rollback-to-last-green behavior.

## Create or update these exact files

- `agents/lib/controller_repair.py`
- `agents/lib/check_runner.py`
- `agents/lib/batch_executor.py`
- `agents/lib/failure_journal.py`
- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `tests/test_task_queue.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The stronger self-heal surface should, at minimum:

1. rank candidate repair plans using bounded deterministic signals
2. record last-green validation truth before broader repair attempts
3. allow bounded rollback when a repair regresses validation or branch posture
4. preserve duplicate-attempt suppression instead of replacing it
5. avoid silently escalating into unbounded speculative rewrites

## Acceptance

This task is complete when repair planning can rank bounded repair options, roll back to a known last-green state when necessary, and prove those behaviors through focused tests.
