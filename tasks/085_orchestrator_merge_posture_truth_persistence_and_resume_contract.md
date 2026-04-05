# Task 085 — Orchestrator merge-posture truth persistence and resume contract

## Why this task exists

Accepted-task autonomous merge/reset posture now exists, but it must be made fully canonical as a persisted truth surface so resume behavior depends on actual evidence rather than inferred success.

## Outcome

Treat merge-posture outcomes as first-class terminal truth and make resume-after-merge depend on persisted evidence.

## Create or update these exact files

- `agents/lib/batch_state.py`
- `agents/lib/batch_executor.py`
- `agents/lib/git_workflow.py`
- `agents/lib/task_queue.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) First-class merge-posture terminal decisions

The controller contract must explicitly support and persist:

- `failed_merge`
- `failed_checks`
- `failed_reset`

### 2) Accepted-task PR flow truth fields

Persisted task/checkpoint truth must include at least:

- `accepted_task_pr_flow_completed`
- `required_checks_passed`
- `merged_to_main`
- `clean_main_reset_completed`

### 3) Resume-after-merge gate

`resume_after_merge` may skip prior tasks only when persisted evidence proves:

- terminal status was completed
- acceptance decision was accepted
- merged-to-main is true
- clean-main-reset-completed is true

### 4) Resume-after-manual-resolution gate

Manual/blocked tasks must not be skipped implicitly. Resume after manual resolution must continue to require explicit operator intent and persisted resume metadata.

## Tests

Add/adjust tests that prove:

1. merge-posture failures stop honestly and persist terminal truth
2. resume-after-merge only skips tasks with accepted+merged+reset-clean evidence
3. manual/blocked recovery still requires explicit resume posture
4. persisted state exposes merge/reset truth and resume metadata consistently

## Guardrails

- Do not silently coerce merge/reset failures into `continue`
- Do not skip tasks on resume without persisted proof
- Keep resume behavior deterministic and auditable

## Acceptance

This task is complete when merge posture is a first-class persisted truth surface and resume behavior depends on that truth rather than inference.
