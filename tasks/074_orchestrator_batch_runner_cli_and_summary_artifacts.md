# Task 074 — Orchestrator batch runner CLI and summary artifacts

## Why this task exists

After the queue model, state persistence, isolation policy, and continue gate exist, the orchestrator needs a user-facing way to run a list of tasks and understand what happened.

## Outcome

Add a narrow batch runner CLI surface plus summary artifacts that make sequential task-list execution visible and reviewable.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/task_queue.py`
- `agents/lib/batch_state.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `README.md`

## Required behavior

### 1) Batch runner entry

Add a CLI mode or argument surface that can accept a task-list manifest and begin sequential execution.

This first version may remain conservative and may stop after the first blocking/manual outcome.

### 2) Summary artifact

Write a machine-readable batch summary artifact capturing at least:

- manifest path
- total tasks
- completed tasks
- failed/manual/blocked tasks
- final batch decision
- per-task short outcomes

### 3) Human-readable summary

Emit a concise human-readable summary at the end of the batch run so a user can see what happened without reading raw state files.

### 4) Preserve single-task entrypoint behavior

Single-task usage must continue to work as before.

## Tests

Add coverage that proves:

1. the batch CLI surface parses correctly
2. a short queue can run sequentially through the batch runner
3. the batch summary artifact is written with expected fields
4. single-task behavior remains intact

## Documentation

Update the product spec and root README to describe the first batch-runner CLI mode and summary artifacts.

## Guardrails

- Do not attempt broad concurrent batch execution
- Keep the first batch runner conservative and reviewable
- Prefer clear summaries over noisy verbose logging

## Acceptance

This task is complete when:

- a task-list manifest can be executed through a batch runner CLI
- a batch summary artifact is written
- a concise human-readable summary is emitted
- single-task behavior is preserved
- tests remain green
