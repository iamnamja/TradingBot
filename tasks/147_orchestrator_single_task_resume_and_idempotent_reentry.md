# Task 147 — Orchestrator single-task resume and idempotent re-entry

## Goal
Make the bounded single-task lane safe to resume after interruption without duplicating work, losing artifacts, or double-counting run outcomes.

## Scope
- bounded one-task resume/re-entry only
- deterministic artifact preservation
- no multi-task unattended expansion

## Create or update these exact files
- `agents/run_single_task.py`
- `agents/lib/failure_journal.py`
- `agents/run_task.py`
- `tests/test_single_task_runner.py`
- `tests/test_failure_journal.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Required behavior
If the bounded runner is interrupted after admission or during validation/reporting, a resumed attempt should either safely continue or deterministically restart that one task, without emitting duplicate ledger rows, duplicate handoff artifacts, or widened execution scope.

## Acceptance
This task is complete when one-task safe-lane runs have an honest resume contract and idempotent re-entry posture that preserves bounded artifacts and execution truth.
