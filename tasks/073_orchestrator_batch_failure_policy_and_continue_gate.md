# Task 073 — Orchestrator batch failure policy and continue gate

## Why this task exists

A task-list runner needs a deterministic policy for what happens after each task. Some failures should stop the queue, others should require manual intervention, and some conditions may allow the orchestrator to continue.

## Outcome

Introduce an explicit continue/stop/manual gate for batch execution, grounded in the failure classification and remediation signals already added earlier in the project.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/task_queue.py`
- `agents/lib/batch_state.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Required behavior

### 1) Explicit post-task decision gate

After each queued task, compute a narrow batch decision such as:

- `continue`
- `stop`
- `manual_patch`
- `blocked`

### 2) Grounding signals

Base that decision on existing runtime signals where possible, including:

- validator success/failure
- deliverable completeness violations
- protected-lane failures
- duplicate bundle conflict artifacts
- manual patch recommendations

### 3) No silent continuation past hard failures

The queue must not silently continue when the result indicates a hard failure or manual patch path.

### 4) Batch-state integration

Persist the post-task decision in batch state so resume logic knows whether the queue may continue automatically.

## Tests

Add coverage that proves:

1. successful tasks produce a `continue` decision
2. manual-patch-class failures produce `manual_patch`
3. hard failures produce `stop` or `blocked` according to the chosen rule
4. batch state persists the decision deterministically

## Documentation

Update the controls/policies doc to explain the batch continue gate and when the queue stops versus continues.

## Guardrails

- Do not guess continuation rules from vague text
- Prefer explicit, test-backed policy decisions
- Keep the first continue gate conservative

## Acceptance

This task is complete when:

- post-task batch decisions are explicit and persisted
- manual-patch and hard-failure paths do not silently continue
- tests remain green
