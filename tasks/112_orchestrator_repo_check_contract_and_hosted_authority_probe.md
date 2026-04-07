# Task 112 — Orchestrator repo check contract and hosted-authority probe

## Why this task exists

Hosted CI authority is now modeled in truth surfaces, but live PR behavior still often reports `no checks reported on the branch`. The repo needs a stronger required-check contract and probe lane.

## Outcome

Add a repo-scoped check contract and stronger hosted-authority probe behavior that remains truthful when checks are missing, misconfigured, or unavailable.

## Create or update these exact files

- `agents/lib/git_workflow.py`
- `agents/lib/batch_state.py`
- `agents/run_task.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The repo check contract should, at minimum:

1. support one repo-scoped source of truth for required checks
2. distinguish unavailable vs misconfigured vs reported-but-unsatisfied hosted authority
3. keep `no checks reported` as an explicit non-success signal
4. persist probe truth in batch/checkpoint state
5. avoid over-claiming that hosted CI is stronger than it really is in the live repo

## Acceptance

This task is complete when hosted-authority probe behavior is grounded in an explicit repo check contract and focused tests prove truthful non-success handling for missing or unavailable hosted checks.
