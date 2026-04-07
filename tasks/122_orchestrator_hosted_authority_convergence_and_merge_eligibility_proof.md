# Task 122 — Orchestrator hosted authority convergence and merge eligibility proof

## Why this task exists

The orchestrator now models hosted authority more honestly, but live repo behavior still shows that operational merge truth is weaker than the controller would like.

## Outcome

Add hosted-authority convergence and explicit merge-eligibility proof behavior grounded in real required-check contracts.

## Create or update these exact files

- `agents/lib/git_workflow.py`
- `agents/lib/batch_state.py`
- `agents/lib/controller_contract.py`
- `agents/run_task.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_controller_contract.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The convergence layer should, at minimum:

1. distinguish local green from hosted merge-eligible truth explicitly
2. ground merge eligibility in required-check contracts and branch-protection semantics where available
3. surface missing, unavailable, misconfigured, or unsatisfied hosted checks as distinct non-success states
4. persist merge-eligibility truth in batch/checkpoint state
5. avoid claiming that a branch is safely mergeable when hosted evidence is still weak or absent

## Acceptance

This task is complete when the repo has focused tests proving truthful merge-eligibility behavior under satisfied, missing, unavailable, and misconfigured hosted-authority conditions.
