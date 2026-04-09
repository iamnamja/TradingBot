# Task 145 — Orchestrator scheduler bridge to safe single-task runner

## Goal
Make the orchestrator use the dedicated bounded one-task runner as its canonical execution path whenever exactly one dependency-ready safe-lane task is admissible.

## Scope
- bridge existing scheduler/controller flow to the bounded runner
- keep self-hosting control-plane work escalation-first
- do not widen beyond one task at a time

## Create or update these exact files
- `agents/lib/batch_executor.py`
- `agents/lib/task_queue.py`
- `agents/run_single_task.py`
- `agents/run_task.py`
- `tests/test_task_queue.py`
- `tests/test_single_task_runner.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Required behavior
When the scheduler/controller selects exactly one dependency-ready allowlisted safe task, it should route through the dedicated single-task runner, preserve the bounded ledger/reporting/handoff behavior, and refuse to widen into multi-task or unsafe execution.

## Acceptance
This task is complete when the orchestrator can honestly say that its scheduler path invokes the bounded one-task runner for a single admissible safe task instead of relying on an ad hoc side utility.
