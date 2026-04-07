# Task 110 — Orchestrator repair memory and duplicate-attempt suppression

## Why this task exists

The orchestrator still repeats near-identical no-progress repair attempts too easily. Self-heal needs memory, not only classification.

## Outcome

Persist repair fingerprints and suppress repeated no-progress repair attempts for the same task/repair surface.

## Create or update these exact files

- `agents/lib/controller_repair.py`
- `agents/lib/failure_journal.py`
- `agents/lib/batch_state.py`
- `agents/lib/batch_executor.py`
- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `tests/test_task_queue.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The repair-memory surface should, at minimum:

1. persist repair fingerprints and target-file surfaces per attempt
2. detect when the next repair plan is effectively the same no-progress plan
3. emit an explicit no-progress signal for controller stop/manual behavior
4. preserve bounded retry budgets
5. avoid silently broadening into unlimited retries

## Acceptance

This task is complete when repeated same-surface repair attempts are detected and suppressed deterministically, with explicit persisted truth and focused tests proving the no-progress stop behavior.
