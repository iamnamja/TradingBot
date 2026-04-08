# Task 140 — Orchestrator single-task canary metrics and reporting

## Goal
Measure whether autonomous single-task runs are actually succeeding by aggregating ledger outcomes into stable canary metrics and recovery reporting.

## Scope
- run ledger aggregation only
- completion rate, retry convergence, stop reasons, hosted-authority blocking frequency
- no broad dashboard or operator app shell yet

## Create or update these exact files
- `agents/lib/failure_journal.py`
- `agents/run_single_task.py`
- `tests/test_failure_journal.py`
- `tests/test_single_task_runner.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/README.md`

## Required behavior
The implementation should produce durable canary metrics from one-task ledger entries so the team can answer whether autonomous runs are converging, where they stop, and how often hosted-authority truth blocks progression. Keep the reporting bounded and artifact-based rather than building a UI.

## Acceptance
This task is complete when the repo can compute stable canary metrics from autonomous single-task runs, focused tests cover the reporting surface, and the docs describe the system as measurable but still bounded.
