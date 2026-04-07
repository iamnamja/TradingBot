# Task 106 — Orchestrator external workspace bootstrap recovery proof

## Why this task exists

The portability proof currently covers a simple external Python workspace, but it should also prove truthful bootstrap failure and recovery.

## Outcome

Add a deterministic proof for a simple external Python workspace that initially fails bootstrap/setup and then recovers truthfully.

## Create or update these exact files

- `agents/lib/project_workspace_adapter.py`
- `agents/lib/multi_agent_loop.py`
- `tests/test_project_bootstrap_adapter.py`
- `tests/test_multi_project_adapters.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `README.md`

## Required behavior

- preserve explicit bootstrap truth (`not_started`, `blocked`, `succeeded`)
- prove resumable recovery after a bootstrap-blocked state
- keep the scope Python-first and deterministic
- do not broaden the claim beyond a simple external Python workspace shape

## Acceptance

This task is complete when the repo has deterministic proof of truthful bootstrap failure and recovery over a simple external Python workspace.
