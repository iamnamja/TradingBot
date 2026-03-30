# Task 075 — Orchestrator backlog execution end-to-end proof

## Why this task exists

The earlier tasks in this tranche add the pieces needed for backlog execution. This final proof task should show that the orchestrator can take a list of tasks, move through them sequentially, persist state, and stop safely when policy says it must.

## Outcome

Add an end-to-end proof for backlog execution over a short manifest of representative tasks.

## Create or update these exact files

- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`

## Required behavior

### 1) Sequential backlog proof

Demonstrate, through tests and supporting runtime behavior, that the orchestrator can:

- load a short manifest
- run tasks in order
- persist batch state between items
- produce summary output
- stop conservatively when a task requires manual intervention or blocking

### 2) Recovery-aware progression

Show that the backlog proof respects the continue gate and does not blindly advance past hard failures.

### 3) Integration with earlier reliability work

The proof should be grounded in the behavior already added earlier, including:

- deliverable completeness enforcement
- protected-lane routing
- duplicate-bundle recovery
- truthful failure artifacts

## Tests

Add E2E-oriented coverage that proves:

1. a short all-success manifest can run to completion
2. a manifest containing a manual-patch or blocked result stops conservatively
3. batch state and summary artifacts reflect the final outcome accurately

## Documentation

Update project state and product spec docs to describe the orchestrator as having a first end-to-end backlog execution proof, while remaining conservative for protected/controller tasks.

## Guardrails

- Do not turn this into a broad production scheduler
- Keep the proof narrow, deterministic, and grounded in testable local behavior
- Prefer conservative stopping over overconfident continuation

## Acceptance

This task is complete when:

- the orchestrator has a test-backed end-to-end proof for short backlog execution
- stop/continue behavior is conservative and explicit
- batch state and summary artifacts match the observed run
- docs reflect the new capability honestly
