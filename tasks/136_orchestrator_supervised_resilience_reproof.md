# Task 136 — Orchestrator supervised resilience re-proof

## Goal
Re-prove the orchestrator over the exact failure classes that have still been causing manual babysitting after Task 129.

## Scope
- bounded supervised local-first execution only
- historical failure corpus including:
  - empty bundle
  - underfilled bundle
  - coupled compatibility/public-surface drift
  - conservative no-ready-task stop posture
  - hosted-authority unsatisfied / missing-check evidence

## Create or update these exact files
- `tests/test_run_task_contract_directives.py`
- `tests/test_run_task_parsers_and_policies.py`
- `tests/test_failure_journal.py`
- `tests/test_project_registry.py`
- `tests/test_task_queue.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `README.md`

## Required behavior
The re-proof should demonstrate only a bounded supervised slice, including at most:

1. admission-time rejection of under-specified proof tasks
2. targeted handling of empty and underfilled bundle failures
3. missing-deliverable retry compilation instead of generic retry wording
4. coupled compatibility-surface repair planning
5. last-known-good subset preservation during retries
6. conservative stop or block posture when hosted authority is absent or unsatisfied
7. no broader claim than the deterministic local supervised proof actually covers

## Acceptance
This task is complete when the repo has a fresh bounded supervised resilience re-proof over these known failure classes, with docs synchronized narrowly and honestly.
