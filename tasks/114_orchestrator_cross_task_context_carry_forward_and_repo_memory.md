# Task 114 — Orchestrator cross-task context carry-forward and repo memory

## Why this task exists

To move through broader manifests with less babysitting, the orchestrator needs bounded memory across tasks: what changed, what was deferred, what remains blocked, and what context should carry forward.

## Outcome

Add cross-task context carry-forward and bounded repo memory for ordinary-manifest execution.

## Create or update these exact files

- `agents/lib/batch_state.py`
- `agents/lib/batch_executor.py`
- `agents/lib/failure_journal.py`
- `agents/lib/manifest_planner.py`
- `agents/run_task.py`
- `tests/test_task_queue.py`
- `tests/test_failure_journal.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The carry-forward surface should, at minimum:

1. persist accepted change summaries and unresolved blockers between tasks
2. carry forward bounded repo memory rather than raw unbounded logs
3. allow deferred issues to remain visible without pretending they are resolved
4. remain deterministic and inspectable
5. support later supervised autonomy proofs without broadening claim scope prematurely

## Acceptance

This task is complete when the repo has bounded cross-task carry-forward memory with focused tests proving the orchestrator can preserve useful prior-task context without losing truthful stop/defer signals.
