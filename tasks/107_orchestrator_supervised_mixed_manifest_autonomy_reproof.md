# Task 107 — Orchestrator supervised mixed-manifest autonomy re-proof

## Why this task exists

After the resilience hardening tasks land, the orchestrator should re-prove itself over a short mixed manifest rather than only isolated proof tasks.

## Outcome

Add a supervised local-first re-proof over a short mixed manifest spanning proof/docs, bootstrap, and consumer-facing task shapes.

## Create or update these exact files

- `tests/test_multi_project_adapters.py`
- `tests/test_project_bootstrap_adapter.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `README.md`

## Required behavior

The mixed-manifest proof should demonstrate only a bounded supervised slice, including at most:

1. short mixed-manifest progression across more than one task family
2. truthful use of routing/planner/bootstrap/verification surfaces together
3. conservative stop behavior when authority is unsatisfied
4. no broader claim than the deterministic proof actually covers

## Acceptance

This task is complete when the repo has a fresh supervised mixed-manifest re-proof after the resilience hardening tranche, with docs synchronized narrowly and honestly.
