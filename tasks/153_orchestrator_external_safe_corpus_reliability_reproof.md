# Task 153 — Orchestrator external safe corpus reliability re-proof

## Goal
Re-prove the bounded one-task lane on the external-safe evaluation corpus and only keep the current autonomy claim if the measured pass-rate and self-heal behavior are good enough.

## Scope
- re-proof only
- no widening beyond one-task autonomy
- use the measured corpus and scoreboard built in Tasks 149–152

## Create or update these exact files
- `tests/test_single_task_runner.py`
- `tests/test_failure_journal.py`
- `tests/test_merge_manager_integration.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_RELIABILITY_AND_AUTONOMY_REVIEW.md`
- `README.md`

## Required behavior
The repo should be able to show that the bounded one-task lane now completes an external-safe corpus at a meaningful supervised pass rate, that self-heal contributes to completion instead of only increasing churn, and that unsafe/self-hosting work still escalates cleanly.

## Acceptance
This task is complete when the project has a fresh reliability re-proof over the external-safe corpus and can truthfully state the current one-task autonomous pass-rate band.
