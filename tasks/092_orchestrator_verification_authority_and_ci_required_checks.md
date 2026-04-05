# Task 092 — Orchestrator verification authority and CI required checks

## Why this task exists

Today the orchestrator can run local validation and optionally drive PR/check/merge/reset posture, but the end-state product needs stronger verification authority than local-only green runs.

To make unattended merge behavior more trustworthy, the orchestrator must treat GitHub-required CI checks as first-class evidence rather than a best-effort add-on.

## Outcome

Make CI-required checks and verification authority explicit in the multi-agent controller loop.

## Create or update these exact files

- `agents/lib/git_workflow.py`
- `agents/lib/multi_agent_loop.py`
- `agents/lib/batch_state.py`
- `agents/run_task.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Explicit verification authority profile

Introduce a canonical verification-authority profile that can represent at least:

- local_only
- local_plus_required_ci
- required_ci_only (if local checks are intentionally skipped)

### 2) Required-check truth

The orchestrator must persist and reason over:

- whether required checks were discovered
- whether any required checks are missing
- whether checks are pending / timed out / failed / passed
- whether missing-check posture should block merge

### 3) Truthful stop posture

If required CI checks are configured but do not report success, the orchestrator must stop honestly and persist non-proceed state.

### 4) Verifier/controller integration

Verifier evidence and GitHub-required-check evidence should both feed the controller decision rather than existing as unrelated lanes.

## Tests

Add or adjust deterministic tests that prove:

1. required-check state is persisted explicitly
2. merge cannot proceed when required checks are missing or failed
3. local green alone is not treated as sufficient when required CI is configured
4. controller decisions reflect the configured verification-authority profile truthfully

## Guardrails

- Do not fake CI authority where it is not configured
- Keep honest stop posture for missing-check and timeout cases
- Preserve existing merge/reset truth fields rather than inventing parallel ones
- Treat this as a trust-hardening task, not a broader autonomy claim

## Acceptance

This task is complete when the orchestrator can truthfully treat required CI checks as a first-class merge authority and persist that evidence in controller state.
