# Task 095 — Orchestrator dependency-aware manifest planner

## Why this task exists

An ordered list is enough for the current short-manifest proof, but it is too brittle for larger project creation. The orchestrator needs to understand dependencies, blocked tasks, and defer/split behavior so it can work through a broader project backlog more intelligently.

## Outcome

Add a dependency-aware manifest planner that can reason about task prerequisites and blocked execution.

## Create or update these exact files

- `agents/lib/manifest_planner.py`
- `agents/lib/task_queue.py`
- `agents/lib/batch_state.py`
- `agents/run_task.py`
- `tests/test_task_queue.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Canonical dependency surface

Support a manifest/task surface that can represent at least:

- depends_on
- blocks
- optional / deferrable tasks
- skipped-by-policy tasks
- re-run required because prerequisite changed

### 2) Honest blocked posture

Blocked tasks must be surfaced explicitly rather than being treated as silent failures or arbitrary ordering problems.

### 3) Conservative reordering

The planner may choose a safer ready task, but only when that does not violate explicit dependency truth.

### 4) Resume compatibility

Persist enough dependency/planner truth that resume behavior remains deterministic.

## Tests

Add or adjust deterministic tests that prove:

1. dependency-aware manifests can identify ready vs blocked tasks
2. controller can defer blocked tasks without corrupting queue truth
3. safer reordering is possible only when dependency rules allow it
4. resume can reconstruct planner truth deterministically

## Guardrails

- Do not turn this into speculative broad scheduling
- Keep planner decisions explicit and persisted
- Preserve current stop posture for true blocking conditions
- Prefer truthful dependency semantics over aggressive throughput

## Acceptance

This task is complete when the orchestrator can plan and persist dependency-aware manifest progression rather than relying only on a fixed ordered list.
