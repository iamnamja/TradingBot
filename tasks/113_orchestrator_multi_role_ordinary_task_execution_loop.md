# Task 113 — Orchestrator multi-role ordinary-task execution loop

## Why this task exists

The current multi-agent loop is still strongest as a proof-facing surface. The next step is a stronger ordinary-task execution loop with explicit builder/tester/controller coordination.

## Outcome

Add a stronger multi-role ordinary-task execution loop that uses coder/tester/controller artifacts together on ordinary tasks while remaining sequential and bounded.

## Create or update these exact files

- `agents/lib/multi_agent_loop.py`
- `agents/lib/controller_contract.py`
- `agents/lib/check_runner.py`
- `agents/lib/final_acceptance.py`
- `agents/run_task.py`
- `tests/test_multi_project_adapters.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The loop should, at minimum:

1. execute a builder step, then tester step, then controller decision step
2. allow tester-focused replay before broader validation when appropriate
3. preserve controller-owned final continue/stop authority
4. remain bounded and local-first
5. avoid claiming broad unattended autonomy for protected or meta task families

## Acceptance

This task is complete when the repo has a stronger multi-role ordinary-task execution surface proven through focused tests, while staying within the current bounded autonomy posture.
