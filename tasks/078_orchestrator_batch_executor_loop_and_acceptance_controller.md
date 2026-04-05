# Task 078 — Orchestrator batch executor loop and acceptance controller

## Why this task exists

074 introduced a conservative batch runner CLI and 075 proved a narrow short-manifest slice under tests, but the controller still does not own a clean, explicit per-task batch execution loop that:

- runs a task
- applies final acceptance review
- retries self-heal when safe
- persists state and short outcomes
- then advances or stops conservatively

That logic should exist as a first-class controller surface rather than only as scattered proof behavior.

## Outcome

Add a dedicated batch executor/controller loop that uses the final acceptance reviewer and current queue/state surfaces to process one task at a time through a manifest.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/batch_executor.py`
- `agents/lib/batch_state.py`
- `agents/lib/task_queue.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Explicit per-task batch loop

For each queued task, the executor should:

1. start task execution
2. run authoritative validation
3. run final acceptance review
4. retry self-heal if acceptance is retryable and budget remains
5. persist per-task final decision/outcome
6. either advance to next task or stop conservatively

### 2) Per-task outcome persistence

Persist at least:

- task path
- terminal status
- final acceptance decision
- retry count
- whether the next task may proceed

### 3) Preserve single-task entrypoint behavior

Do not break ordinary single-task usage.

### 4) Conservative stop posture

If a task reaches `manual_patch` or `blocked`, the executor must stop and persist that clearly.

## Tests

Add coverage that proves:

1. a short batch loop advances through two accepted tasks
2. a retryable acceptance failure consumes budget and then succeeds
3. a manual/blocked task stops the loop conservatively
4. persisted state reflects the final per-task decisions accurately

## Documentation

Update the product spec and project state docs to describe the batch executor/controller loop as the canonical path for sequential manifest execution.

## Guardrails

- Keep the executor sequential and deterministic
- Do not add concurrent scheduling
- Prefer explicit persisted decisions over implicit controller state

## Acceptance

This task is complete when:

- a dedicated batch executor/controller loop exists
- it uses final acceptance review before advancing
- per-task outcomes are persisted explicitly
- tests prove accepted/retryable/manual-stop behavior
- docs reflect the new controller surface honestly
