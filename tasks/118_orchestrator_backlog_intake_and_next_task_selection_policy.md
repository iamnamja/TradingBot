# Task 118 — Orchestrator backlog intake and next-task selection policy

## Why this task exists

The orchestrator can execute a bounded manifest, but it still does not have a strong policy for deciding what should happen next across a real backlog.

## Outcome

Add backlog intake and explicit next-task selection policy for project backlogs.

## Create or update these exact files

- `agents/lib/task_queue.py`
- `agents/lib/controller_contract.py`
- `agents/lib/manifest_planner.py`
- `agents/lib/project_registry.py`
- `agents/run_task.py`
- `tests/test_task_queue.py`
- `tests/test_controller_contract.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The next-task selector should, at minimum:

1. rank backlog items using explicit priority, readiness, and blocked-state signals
2. refuse to schedule tasks whose dependencies or authority prerequisites are unsatisfied
3. use bounded carry-forward memory as an input rather than only manifest order
4. emit explicit selection truth explaining why the chosen task was selected or skipped
5. remain deterministic and inspectable under test

## Acceptance

This task is complete when the controller can choose the next task from a backlog using explicit selection policy and focused tests prove deterministic skip/select behavior across ready and blocked tasks.
