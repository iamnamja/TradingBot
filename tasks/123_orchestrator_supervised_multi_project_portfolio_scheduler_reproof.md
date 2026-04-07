# Task 123 — Orchestrator supervised multi-project portfolio scheduler re-proof

## Why this task exists

After project registry, isolation, next-task policy, dependency planning, stronger self-heal, project-aware validation, and hosted-authority convergence land, the orchestrator should re-prove itself over a bounded portfolio slice spanning more than one project.

## Outcome

Add a supervised local-first multi-project portfolio scheduler re-proof that demonstrates project selection, isolated state, next-task choice, and conservative stop behavior across more than one project.

## Create or update these exact files

- `tests/test_project_registry.py`
- `tests/test_task_queue.py`
- `tests/test_multi_project_adapters.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_failure_journal.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `README.md`

## Required behavior

The re-proof should demonstrate only a bounded supervised slice, including at most:

1. project selection across more than one registered project
2. isolated per-project state, branch, workspace, and carry-forward memory
3. next-task choice driven by explicit backlog policy and dependency truth
4. stronger self-heal with bounded repair planning and rollback where relevant
5. project-aware validation and authority evaluation
6. conservative stop behavior when portfolio scheduling or merge authority is unsatisfied
7. no broader claim than the deterministic local supervised proof actually covers

## Acceptance

This task is complete when the repo has a fresh supervised local-first re-proof over a bounded multi-project portfolio slice after Tasks 116–122, with docs synchronized narrowly and honestly.
