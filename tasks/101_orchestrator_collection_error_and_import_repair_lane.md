# Task 101 — Orchestrator collection-error and import-repair lane

## Why this task exists

The recent misses on 097 and 099 failed during pytest collection before deeper verifier/controller evidence could help.

Collection-time import/symbol failures need their own repair lane.

## Outcome

Add a first-class repair path for pytest collection-time failures such as missing imports, bad module references, missing exported symbols, and similar pre-test failures.

## Create or update these exact files

- `agents/lib/controller_repair.py`
- `agents/lib/failure_journal.py`
- `agents/lib/multi_agent_loop.py`
- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

- detect collection-time failures distinctly from normal failing tests
- route them through an explicit narrow repair strategy
- journal the classification explicitly
- avoid broad rewrites when the failure is a missing symbol/import mismatch

## Acceptance

This task is complete when collection-time import/public-surface failures are recognized and routed as their own first-class repair lane.
