# Task 143 — Orchestrator GitHub settle-window and dual-surface probe

## Goal
Make hosted-authority interpretation operationally reliable by distinguishing initial GitHub reporting delay from genuine missing required-check evidence.

## Scope
- narrow GitHub operational-convergence hardening only
- no widening of autonomous task-family scope
- preserve the stable required-check contract around `ci-required`

## Create or update these exact files
- `agents/lib/git_workflow.py`
- `agents/run_task.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_GITHUB_REQUIRED_CHECK_SETUP.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`

## Required behavior
The hosted-authority probe should tolerate an initial settle window, read both check runs and commit-status surfaces, distinguish `not yet reported` from `required context missing`, and keep the repo truthful when `ci-required` never appears or never turns green.

## Acceptance
This task is complete when live-GitHub interpretation no longer treats the first `no checks reported` signal as final truth, while still blocking unattended-readiness claims until the stable `ci-required` contract is actually satisfied.
