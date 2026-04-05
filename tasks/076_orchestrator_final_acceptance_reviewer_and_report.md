# Task 076 — Orchestrator final acceptance reviewer and report

## Why this task exists

The 074a–075 work materially improved the definition of “green,” but the final acceptance logic is still spread across controller flow in `agents/run_task.py` and ad hoc runtime/tests. The next step is to make the final “did this task truly finish?” review explicit, structured, and reusable.

## Outcome

Extract a dedicated final-acceptance reviewer and a machine-readable acceptance report that compares:

- what the task contract required
- what the committed branch `HEAD` actually changed
- whether the authoritative validation profile passed
- whether unexpected tracked artifacts remain

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/final_acceptance.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Dedicated final acceptance reviewer

Add a narrow module that can evaluate final task acceptance from repo-local facts.

The reviewer should consume at least:

- task file path
- validated exact required paths
- committed `HEAD` diff paths
- working-tree diff paths
- authoritative validation profile result
- unexpected tracked artifact findings

### 2) Machine-readable acceptance report

Produce a report object or dict with at least:

- `task_file`
- `acceptance_decision`
- `required_paths`
- `head_diff_paths`
- `working_tree_paths`
- `validation_profile`
- `issues`
- `retryable`
- `manual_patch_required`

### 3) Explicit acceptance outcomes

The reviewer should classify outcomes conservatively, using a small explicit set such as:

- `accepted`
- `retryable_failure`
- `manual_patch`
- `blocked`

### 4) Keep controller shell thin

`agents/run_task.py` may still call into the acceptance reviewer, but the reusable policy/review logic should live outside the monolithic shell file.

## Tests

Add coverage that proves:

1. an accepted task yields an `accepted` final report
2. missing required files in committed `HEAD` produce a rejecting report
3. unexpected tracked artifacts in committed diff produce a rejecting report
4. merge-ready validation failure is surfaced distinctly from task-contract mismatch

## Documentation

Update controls/policies and project state docs to describe the final acceptance reviewer as the canonical place where task contract, committed diff, and final validation are reconciled.

## Guardrails

- Keep the acceptance outcome set intentionally small
- Prefer explicit rejection over optimistic acceptance
- Do not turn this into a broad workflow engine yet
- Preserve current single-task behavior while improving the final review surface

## Acceptance

This task is complete when:

- final acceptance review is implemented in a dedicated helper/module
- a machine-readable acceptance report exists
- acceptance outcomes are explicit and conservative
- tests cover accepted, retryable, and blocked/manual cases
- docs describe the new reviewer honestly
