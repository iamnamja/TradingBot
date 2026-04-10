# Task 151 — Orchestrator external safe failure taxonomy and self-heal router

## Goal
Teach the bounded one-task lane to classify ordinary external-safe failures and select the smallest credible self-heal action instead of relying on generic retries.

## Scope
- external-safe corpus failures only
- no broad autonomy widening
- target the highest-frequency ordinary coding failure classes first

## Create or update these exact files
- `agents/lib/failure_classifier.py`
- `agents/lib/repair_planner.py`
- `agents/run_single_task.py`
- `tests/test_failure_classifier.py`
- `tests/test_single_task_runner.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_RELIABILITY_AND_AUTONOMY_REVIEW.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Required behavior
The orchestrator should distinguish common one-task external-safe failures such as missing file updates, test regressions, import/collection errors, incomplete deliverable coverage, and formatting/lint-only failures, then choose a targeted self-heal lane with bounded retries and explicit evidence.

## Acceptance
This task is complete when the one-task lane can route ordinary external-safe failures into a concrete self-heal plan that is narrower and more reliable than a generic replay.
