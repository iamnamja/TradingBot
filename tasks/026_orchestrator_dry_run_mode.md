# Task 026: Orchestrator dry-run mode

## Goal
Add a dry-run / simulation mode so the orchestrator can show what it would do without mutating repo or PR state.

## Deliverables
- updates to orchestrator runner/CLI as needed:
  - `src/builder/orchestrator/runner.py`
  - `src/builder/orchestrator/cli.py`

- `tests/test_orchestrator_dry_run.py`

## Existing repo dependencies (NOT deliverables)
Reuse the orchestrator modules already built:
- runner
- cli
- audit
- project adapter/config
- merge manager
- repair workflow

Do **not** implement dry-run mode by patching or reusing unrelated TradingBot application entrypoints such as `tradingbot.run`.

## Scope and compatibility
This task extends the orchestrator layer built in earlier tasks.
It must remain compatible with the established non-dry-run behavior from Task 021.

This is the most important compatibility rule in the task:
- if no pending task exists in normal mode, `run_next_task()` must continue to return:
  - `task_name = "none"`
  - `status = "no_task"`

Dry-run mode must **not** break that existing behavior.

## Required behavior

### Dry-run mode
The orchestrator should:
- load config and state
- select the next task
- evaluate what actions would be taken
- return a structured dry-run plan
- avoid mutating git branches, PRs, or remote state

### Mutation boundary
In dry-run mode, the orchestrator must not call mutation methods such as:
- create branch
- push branch
- create PR
- merge PR
- write remote state

Tests should verify these mutation methods are not called.

### Correct test target
Tests must exercise the orchestrator entrypoint and/or orchestrator runner created in previous tasks.

They must **not** patch:
- `tradingbot.run`
- unrelated broker clients
- unrelated paper-trading code paths

### Return-shape contract
Dry-run results must use deterministic primitive fields.

For dry-run mode, include at least:
- `dry_run: bool`
- `task_name: str`
- `status: str`
- `message: str`

Optional:
- `planned_actions: list[str]`

### No-pending-task contract
If no pending task exists:
- normal mode should return:
  - `task_name = "none"`
  - `status = "no_task"`
- dry-run mode should return:
  - `task_name = "none"`
  - `status = "no_task"`
  - `dry_run = True`

Do **not** reuse `"planned"` as the status for the no-task case.

### Dry-run planned-task contract
If a pending task exists in dry-run mode:
- `dry_run = True`
- `task_name` is the selected task name
- `status = "planned"`

### Audit
Dry-run decisions may be auditable through the decision journal if that integration is already available.
If audit integration is included, tests should use temp paths and verify no repo-root artifacts are created.

## Normative examples

### Example 1: pending task in dry-run
- next task is `023_example`
- dry-run returns:
  - `dry_run = True`
  - `task_name = "023_example"`
  - `status = "planned"`

### Example 2: no pending task in dry-run
- no task available
- dry-run returns:
  - `dry_run = True`
  - `task_name = "none"`
  - `status = "no_task"`

### Example 3: mutation boundary
- merge manager / mutation collaborator is injected as a mock
- running dry-run does **not** call:
  - `create_pr`
  - `merge_pr`
  - `sync_main`

### Example 4: test assertions
- tests assert on plain strings / booleans / lists
- tests do not assert on `MagicMock` repr output

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- dry-run mode does not mutate external state
- dry-run output clearly communicates the intended actions
- tests verify the mutation boundary above
- tests target the orchestrator layer, not unrelated TradingBot runtime code
- implementation preserves the established non-dry-run no-task behavior
