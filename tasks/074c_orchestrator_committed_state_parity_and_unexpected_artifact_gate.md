# Task 074c — Orchestrator committed-state parity and unexpected-artifact gate

## Why this task exists

Recent tasks have shown that even after tests are green, the branch may still not be merge-ready because:

- exact required files were not all committed into `HEAD`
- local working-tree changes were still present after validation
- unexpected tracked artifacts (for example `artifacts/*.json`) appeared in the branch diff even though the task did not require them

Before proceeding to the first user-facing batch runner CLI, the orchestrator needs a final committed-state parity gate.

## Outcome

Require final success to mean that the tested state matches committed `HEAD`, exact required deliverables are present in the branch diff, and unexpected tracked artifacts are rejected or cleaned before completion.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/task_contracts.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Committed-state parity gate

Before final success/push, the orchestrator must verify that the state it just validated is the same state represented by committed `HEAD`.

If local modifications that affect required deliverables remain after validation, the task must not be considered complete.

### 2) Exact required deliverable parity

The final committed branch diff must still satisfy the exact required-file contract for the task.

### 3) Unexpected artifact rejection

If tracked branch-diff files appear that are not part of the task’s exact required deliverables, the run must not silently accept them as successful output.

The implementation may clean or exclude known accidental artifacts where safe, but must not report success while unexpected tracked files remain in the final diff.

## Tests

Add coverage that proves:

1. final success is blocked when required deliverables are only present in the working tree but not committed into `HEAD`
2. final success is blocked when unexpected tracked artifacts remain in the branch diff
3. final success is allowed only when committed `HEAD` matches the validated merge-ready state

## Documentation

Update controls/policies and project-state docs to state that autonomous completion now requires committed-state parity and rejection of unexpected tracked artifacts.

## Guardrails

- Do not implement a broad artifact allowlist beyond what current tasks require
- Keep the gate deterministic and repo-local
- Prefer explicit failure/cleanup over silently merging extra files

## Acceptance

This task is complete when:

- final success requires committed-state parity
- exact required deliverables are checked against committed `HEAD`
- unexpected tracked artifacts cannot survive into a supposedly complete branch
