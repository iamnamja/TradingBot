# Task 116 — Orchestrator project registry and per-project contract

## Why this task exists

The orchestrator now has bounded portability proof, but it still lacks one canonical place to describe what a project is, how it should be validated, which autonomy lane it allows, and what workspace/branch assumptions apply.

## Outcome

Add a canonical project registry and per-project contract surface that the controller and runtime can consume directly.

## Create or update these exact files

- `agents/lib/project_registry.py`
- `agents/lib/project_workspace_adapter.py`
- `agents/lib/task_contracts.py`
- `agents/run_task.py`
- `tests/test_project_registry.py`
- `tests/test_multi_project_adapters.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The project registry should, at minimum:

1. define a stable project id and repo root for each registered project
2. declare workspace type, validation contract, branch policy, and allowed autonomy lane per project
3. support the current monorepo plus at least one generic external Python project contract
4. remain deterministic and serializable rather than relying on ad hoc runtime dicts
5. avoid claiming that every registered project is safe for unattended execution

## Acceptance

This task is complete when the repo has one canonical project-registry contract with focused tests proving that per-project validation and autonomy posture can be resolved without hard-coded monorepo assumptions.
