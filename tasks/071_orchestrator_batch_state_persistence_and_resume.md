# Task 071 — Orchestrator batch state persistence and resume

## Why this task exists

Once the orchestrator can represent a task queue, it needs to remember progress across a task list. Long autonomous runs are not credible if progress is lost between tasks or after failures.

## Outcome

Persist task-list execution state so the orchestrator can resume a partially completed queue safely.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/task_queue.py`
- `agents/lib/batch_state.py`
- `tests/test_task_queue.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`

## Required behavior

### 1) Batch state file

Persist machine-readable batch state capturing at least:

- manifest identity or source path
- ordered queue items
- current index
- per-task status
- timestamps or counters sufficient for deterministic resume

### 2) Resume behavior

Support:

- starting a new batch state from a manifest
- resuming an interrupted batch state
- preventing accidental resume against a mismatched manifest without a clear rule

### 3) Safe state transitions

State transitions should be deterministic and narrow, for example:

- `queued` → `running`
- `running` → `completed`
- `running` → `failed`
- `running` → `manual_patch`
- `running` → `blocked`

### 4) Preserve single-task behavior

Do not regress the current single-task flow. Batch state should layer on top of the current controller rather than replace it in one step.

## Tests

Add coverage that proves:

1. a new manifest can initialize batch state
2. batch state can resume from a partially completed queue
3. mismatched manifest/state combinations are handled clearly
4. task status transitions are deterministic and stable

## Documentation

Update the product spec to describe batch state persistence and how resume works for task lists.

## Guardrails

- Do not implement speculative parallel batch execution
- Do not couple state persistence tightly to git history or external services
- Prefer a narrow machine-readable state file that later tasks can reuse

## Acceptance

This task is complete when:

- batch execution state can be persisted and resumed safely
- queue item transitions are explicit and deterministic
- single-task behavior is preserved
- tests remain green
