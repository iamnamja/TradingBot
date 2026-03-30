# Task 072 — Orchestrator per-task checkpoint and branch isolation

## Why this task exists

If the orchestrator is going to work through a list of tasks, it needs clear boundaries between tasks. One task should not silently contaminate the next.

## Outcome

Add narrow per-task checkpointing and branch/worktree isolation rules for batch execution, without yet introducing heavy parallel execution.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/task_queue.py`
- `agents/lib/batch_state.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_VISION_AND_CONTROLS.md`

## Required behavior

### 1) Per-task checkpoint model

Before a queued task starts, the orchestrator should record enough checkpoint information to reason about:

- the branch or worktree context used
- whether the task completed cleanly
- whether cleanup/reset is required before the next task

### 2) Isolation policy

Document and enforce a narrow policy such as:

- one task executes against one clear branch/worktree context
- the next task does not start until the previous task is committed/merged, reset, or explicitly marked blocked/manual
- batch state records which path occurred

### 3) Failure-aware transition

If a task fails or needs manual patching, the batch runner should not silently continue without recording that checkpoint outcome.

### 4) Keep the implementation incremental

This task is about checkpointing/isolation rules and recorded state, not a full-blown worktree manager redesign.

## Tests

Add coverage that proves:

1. per-task checkpoint information is recorded deterministically
2. successful task completion records a clean checkpoint transition
3. failed/manual_patch tasks record an isolation-relevant checkpoint outcome
4. queue state reflects whether the next task may proceed

## Documentation

Update the vision/controls doc to describe the per-task isolation policy for future batch execution.

## Guardrails

- Do not add speculative multi-task concurrency
- Do not weaken existing clean-worktree guardrails
- Prefer explicit checkpoint records over hidden implicit state

## Acceptance

This task is complete when:

- per-task checkpoint/isolation data is recorded
- queue state captures whether progression to the next task is allowed
- documentation reflects the isolation policy
- tests remain green
