# Task 103 — Orchestrator real hosted CI authority integration

## Why this task exists

The code now models verification-authority truth, but branch flows have still shown “no checks reported on the branch” in practice.

The next step is to strengthen real hosted CI authority behavior, not just local semantics.

## Outcome

Make required-check discovery and blocking behavior stronger in real integrated branch/PR flows.

## Create or update these exact files

- `agents/lib/git_workflow.py`
- `agents/lib/multi_agent_loop.py`
- `agents/lib/batch_state.py`
- `agents/run_task.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

- treat hosted required-check discovery as first-class evidence
- distinguish missing discovery from passed authority cleanly
- persist hosted-authority truth explicitly
- stop honestly when configured hosted authority is absent or unsatisfied

## Acceptance

This task is complete when hosted CI authority is stronger and more explicit in real branch/PR semantics, not only in local truth models.
