# Task 142 — Orchestrator supervised safe-lane single-task re-proof

## Goal
Re-prove the orchestrator over the new safe autonomous single-task lane after Tasks 137–141 land.

## Scope
- bounded supervised local-first execution only
- allowlisted single-task autonomy only
- real hosted-authority readiness truth still blocks broader unattended claims

## Create or update these exact files
- `tests/test_run_task_contract_directives.py`
- `tests/test_single_task_runner.py`
- `tests/test_failure_journal.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `README.md`

## Required behavior
The re-proof should demonstrate only a bounded supervised one-task autonomous lane, including at most: allowlisted admission, deterministic single-task runner behavior, stable run ledger and canary metrics, explicit escalation artifacts for unsafe tasks, conservative hosted-authority blocking posture, and no broader claim than the safe lane actually proves.

## Acceptance
This task is complete when the repo has a fresh supervised proof that it can autonomously run one safe task at a time inside the allowlisted lane, with docs synchronized narrowly and honestly.
