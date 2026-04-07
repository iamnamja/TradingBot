# Task 111 — Orchestrator task admission and decomposition gate

## Why this task exists

The current proof slice is still strongest on short ordinary tasks. Broader task shapes need a clearer admission policy and, when appropriate, bounded decomposition before autonomous execution is attempted.

## Outcome

Add task admission, family classification, and bounded decomposition gates for larger or ambiguous task shapes.

## Create or update these exact files

- `agents/lib/agent_router.py`
- `agents/lib/controller_contract.py`
- `agents/lib/task_contracts.py`
- `agents/lib/manifest_planner.py`
- `agents/run_task.py`
- `tests/test_task_queue.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The gate should, at minimum:

1. classify tasks into autonomous-ordinary, supervised-autonomous, or manual-only lanes
2. detect protected/controller/meta task shapes conservatively
3. allow bounded decomposition for larger ordinary tasks without pretending that every task is autonomously admissible
4. persist admission/decomposition truth explicitly
5. remain narrower than any broader autonomy claim in docs

## Acceptance

This task is complete when the repo has explicit task admission truth, bounded decomposition behavior, and focused tests proving conservative routing for protected or ambiguous task shapes.
