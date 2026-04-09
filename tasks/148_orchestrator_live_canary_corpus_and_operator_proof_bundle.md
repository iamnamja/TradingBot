# Task 148 — Orchestrator live canary corpus and operator proof bundle

## Goal
Create the first operator-ready proof bundle for the bounded one-task autonomous lane using a tiny live canary corpus and the real hosted-authority contract.

## Scope
- bounded safe-lane proof bundle only
- supervised operator-facing evidence, not broad autonomy claims
- include both success and explicit escalation cases

## Create or update these exact files
- `agents/run_single_task.py`
- `agents/run_task.py`
- `tests/test_single_task_runner.py`
- `tests/test_failure_journal.py`
- `tests/test_merge_manager_integration.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/ORCHESTRATOR_RELIABILITY_AND_AUTONOMY_REVIEW.md`
- `docs/README.md`
- `README.md`

## Required behavior
The repo should be able to present a tiny proof bundle showing: a live hosted-authority smoke result, one admitted safe task routed through the canonical runner, durable ledger/canary/reporting artifacts, and explicit escalation for work outside the lane.

## Acceptance
This task is complete when the project has an operator-readable bounded proof bundle that supports the honest claim that the orchestrator can run one allowlisted safe task at a time under supervised real-GitHub conditions.
