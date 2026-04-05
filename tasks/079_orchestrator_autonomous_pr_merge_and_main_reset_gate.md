# Task 079 — Orchestrator autonomous PR/merge and main-reset gate

## Why this task exists

To move from “batch proof” toward “runs a list and completes on its own,” the orchestrator needs a safe way to finish an accepted task end to end:

- create PR
- wait for required checks
- merge
- reset/clean `main`
- then continue

Today that lifecycle still depends too much on manual operator steps.

## Outcome

Add an explicit optional PR/merge gate for accepted tasks and the ability to reset back to clean `main` before continuing to the next queued task.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/git_workflow.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `README.md`

## Required behavior

### 1) Accepted-task PR flow

For an accepted task, the orchestrator should be able to:

- create a PR
- watch required checks
- merge only after success

### 2) Safe main reset before next task

After merge, the orchestrator should be able to:

- switch to `main`
- fetch/reset to remote `main`
- clean the worktree
- confirm clean state before continuing

### 3) Honest stop behavior

If PR creation, CI checks, or merge fail, the orchestrator must stop honestly and persist that state rather than pretending the task completed fully.

### 4) Optional/autonomous posture

This should remain a controllable posture, not a hidden always-on side effect.

## Tests

Add coverage that proves:

1. the accepted-task PR flow only proceeds after acceptance
2. merge failure or CI failure stops honestly
3. clean-main reset is required before advancing to the next task
4. single-task mode remains available without batch/merge flow

## Documentation

Update controls/policies, project state, and README to describe the new accepted-task PR/merge posture and its conservative limits.

## Guardrails

- Do not merge tasks that have not passed final acceptance review
- Do not continue to next task unless clean `main` reset succeeds
- Keep behavior explicit and reviewable
- Preserve an operator-controlled mode for merge automation

## Acceptance

This task is complete when:

- accepted tasks can flow through PR/create/check/merge
- clean-main reset is enforced before next-task progression
- failure in PR/CI/merge stops honestly
- docs describe the posture and limits clearly
