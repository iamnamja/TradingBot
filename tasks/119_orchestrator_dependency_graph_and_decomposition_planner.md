# Task 119 — Orchestrator dependency graph and decomposition planner

## Why this task exists

Backlog selection gets more useful only if the orchestrator can understand dependency truth and split larger work into bounded sub-tasks honestly.

## Outcome

Add a dependency graph and bounded decomposition planner for larger multi-step backlog work.

## Create or update these exact files

- `agents/lib/manifest_planner.py`
- `agents/lib/task_contracts.py`
- `agents/lib/controller_contract.py`
- `agents/lib/task_queue.py`
- `agents/run_task.py`
- `tests/test_task_queue.py`
- `tests/test_controller_contract.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The planner should, at minimum:

1. represent dependency edges explicitly between backlog items or decomposed sub-tasks
2. decompose larger work into bounded child tasks when safe rather than flattening it implicitly
3. block scheduling when dependencies are unresolved
4. persist decomposition and dependency truth for resume behavior
5. avoid claiming that all large tasks are safely decomposable

## Acceptance

This task is complete when the repo has an explicit dependency/decomposition planner with focused tests proving honest blocking, bounded splitting, and stable persisted dependency truth.
