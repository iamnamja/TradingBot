# Task 100 — Orchestrator public surface freeze and compatibility aliases

## Why this task exists

Recent proof-task failures showed that collection-time symbol drift is still too easy: tests/docs guessed exported helper names that the current code did not actually stabilize.

The orchestrator now needs an explicit frozen proof-facing/public surface with compatibility aliases where appropriate.

## Outcome

Freeze the proof-facing public surface and add narrowly scoped compatibility aliases so bounded proof tasks stop failing on symbol/name drift.

## Create or update these exact files

- `agents/lib/multi_agent_loop.py`
- `agents/lib/multi_agent_contract.py`
- `agents/lib/project_workspace_adapter.py`
- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_multi_project_adapters.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

- expose one canonical proof-facing symbol set
- add compatibility aliases only where needed for bounded proof surfaces
- keep aliases thin and explicit
- do not silently rename away current canonical symbols without a compatibility bridge

## Acceptance

This task is complete when bounded proof tasks no longer need to guess at exported helper names and the public surface is explicit, tested, and narrow.
