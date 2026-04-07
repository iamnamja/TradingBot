# Task 102 — Orchestrator proof-sync contract validator and claim guard

## Why this task exists

Recent proof-task failures drifted on exported symbols, result fields, manifest schema, and docs claims. These should be caught before full pytest.

## Outcome

Add a proof-sync contract validator that compares exported public surfaces and allowed claim posture before broader proof execution.

## Create or update these exact files

- `agents/lib/controller_contract.py`
- `agents/lib/task_contracts.py`
- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_multi_project_adapters.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `README.md`

## Required behavior

- validate proof-facing exported symbols before full pytest
- validate known result-shape fields used by proof tests
- validate allowed manifest-schema forms where proof tasks rely on them
- prevent docs/README from over-claiming beyond deterministic proof coverage

## Acceptance

This task is complete when proof-sync drift is caught earlier and docs/README claim posture remains explicitly guarded.
