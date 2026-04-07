# Task 117 — Orchestrator project-scoped state, branch, and workspace isolation

## Why this task exists

A portfolio-capable orchestrator cannot allow task state, checkpoint truth, branch naming, or workspace metadata to bleed across projects.

## Outcome

Add project-scoped state, branch, and workspace isolation for batch execution and carry-forward memory.

## Create or update these exact files

- `agents/lib/batch_state.py`
- `agents/lib/task_queue.py`
- `agents/lib/git_workflow.py`
- `agents/lib/project_registry.py`
- `agents/run_task.py`
- `tests/test_task_queue.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The isolation layer should, at minimum:

1. persist state and checkpoints under a stable project-scoped identity
2. isolate branch names and workspace metadata by project
3. prevent carry-forward memory from leaking between unrelated projects
4. keep resume behavior deterministic when more than one project has active state
5. remain conservative when project identity is ambiguous or missing

## Acceptance

This task is complete when batch/checkpoint/branch/workspace truth is isolated by project and focused tests prove that one project cannot accidentally inherit another project's state or carry-forward memory.
