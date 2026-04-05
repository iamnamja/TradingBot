# Task 080 — Orchestrator batch resume after merge and manual resolution

## Why this task exists

Once accepted tasks can merge and the executor can advance, the orchestrator still needs robust resume behavior across two important real-world cases:

- resuming after previously accepted tasks were merged
- resuming after a manual patch / blocked task was resolved outside the current run

Without that, autonomous backlog execution will still be fragile and wasteful.

## Outcome

Add explicit resume semantics for post-merge continuation and manual-resolution recovery.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/batch_executor.py`
- `agents/lib/batch_state.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Resume after accepted merges

If earlier queued tasks were already accepted and merged, the batch resume path should not re-run them unnecessarily.

### 2) Resume after manual intervention

If a task previously ended in `manual_patch` or `blocked`, the operator should be able to resume explicitly after external resolution.

### 3) Explicit resume target and gate

Resume behavior should make clear whether it is:

- resuming the same task
- skipping past an accepted+merged task
- continuing from the next pending queued task

### 4) Truthful persisted state

Persist enough state so that resume decisions are inspectable and deterministic.

## Tests

Add coverage that proves:

1. merged/accepted tasks are not re-run on resume
2. a manually resolved task can be resumed explicitly
3. blocked/manual state is not silently skipped without explicit resume posture
4. persisted state reflects the resume reason and next task accurately

## Documentation

Update product spec and project state docs to describe resume-after-merge and resume-after-manual-resolution semantics.

## Guardrails

- Never silently skip blocked/manual items without explicit operator intent
- Preserve deterministic resume behavior from persisted state
- Keep resume semantics conservative and inspectable

## Acceptance

This task is complete when:

- post-merge and post-manual-resolution resume paths are implemented
- resume targets are explicit and deterministic
- tests cover the main resume cases
- docs reflect the new capability honestly
