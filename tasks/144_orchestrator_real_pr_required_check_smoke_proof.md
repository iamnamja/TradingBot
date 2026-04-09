# Task 144 — Orchestrator real PR required-check smoke proof

## Goal
Add a narrow real-PR smoke proof that records whether the live GitHub ruleset and the stable `ci-required` contract are actually converging on an open pull request.

## Scope
- one small live-PR hosted-authority smoke only
- no broad unattended scheduler claims
- proof remains supervised and explicit

## Create or update these exact files
- `agents/lib/git_workflow.py`
- `agents/run_task.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_GITHUB_REQUIRED_CHECK_SETUP.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `README.md`

## Required behavior
The repo should be able to emit a small artifact or explicit proof result showing whether an open PR reported the stable `ci-required` surface, whether the required-check contract blocked merge until green, and whether hosted authority is now operationally converged enough for the bounded one-task lane.

## Acceptance
This task is complete when the repo has a supervised smoke-proof path for a live PR that can positively demonstrate or honestly fail to demonstrate real `ci-required` convergence.
