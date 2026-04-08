# Task 139 — Orchestrator autonomous single-task runner and ledger

## Goal
Add a dedicated one-task autonomous runner that can execute exactly one admitted safe task and persist a structured run ledger instead of relying on ad hoc shell output alone.

## Scope
- single admitted task only
- run ledger with admission, retries, validation, escalation, and final decision
- no queue-wide or broad unattended progression yet

## Create or update these exact files
- `agents/run_single_task.py`
- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_single_task_runner.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/README.md`

## Required behavior
The runner should accept one task, respect the safe admission lane, execute the bounded local-first flow, and persist a structured ledger entry capturing what happened. The ledger should be deterministic and useful for canary reporting and supervised recovery. This task should not broaden into queue scheduling or a full operator app shell.

## Acceptance
This task is complete when the repo has a dedicated single-task runner with deterministic ledger output, focused tests cover admitted and blocked runs, and the docs describe it as a bounded canary runner rather than broad autonomy.
