# Task 121 — Orchestrator project-aware validation matrix and authority profiles

## Why this task exists

Validation and authority are still too repo-shaped. A multi-project orchestrator needs project-aware focused checks, full checks, bootstrap requirements, and authority profiles.

## Outcome

Add a project-aware validation matrix and authority-profile contract derived from the project registry.

## Create or update these exact files

- `agents/lib/project_registry.py`
- `agents/lib/check_runner.py`
- `agents/lib/git_workflow.py`
- `agents/run_task.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_project_registry.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The validation matrix should, at minimum:

1. allow each project to declare focused checks, full checks, and bootstrap requirements
2. allow each project to declare its verification-authority profile explicitly
3. resolve validation plans from project identity rather than monorepo defaults alone
4. remain truthful when a project has weaker hosted authority than local validation evidence
5. stay serializable and inspectable in persisted state

## Acceptance

This task is complete when validation and authority can be resolved from the project registry per project and focused tests prove that different projects can carry different validation/authority contracts without surface drift.
