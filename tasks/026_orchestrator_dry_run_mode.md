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

This is the most important rule in the task.

## Required behavior

### Dry-run mode
The orchestrator should:
- load config and state
- select the next task
- evaluate what actions would be taken
- print or return a structured plan
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

### Output contract
Tests should assert on deterministic orchestrator-specific output, for example:
- selected task name
- dry-run status
- message/plan fields

Do **not** assert on brittle string representations of `MagicMock` objects.

### Suggested return shape
A dry-run result may include:
- `dry_run: bool`
- `task_name: str`
- `status: str`
- `planned_actions: list[str]`

### Audit
Dry-run decisions should still be auditable through the decision journal if the audit layer is already available.
If audit integration is included, tests should use temp paths and verify no repo-root artifacts are created.

## Normative examples

### Example 1
- next task is `023_example`
- dry-run returns:
  - `dry_run = True`
  - `task_name = "023_example"`
  - `status = "planned"`

### Example 2
- merge manager / mutation collaborator is injected as a mock
- running dry-run does **not** call:
  - `create_pr`
  - `merge_pr`
  - `sync_main`

### Example 3
- tests assert on plain strings / booleans / lists
- tests do not assert on `MagicMock` repr output

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- dry-run mode does not mutate external state
- dry-run output clearly communicates the intended actions
- tests verify the mutation boundary above
- tests target the orchestrator layer, not unrelated TradingBot runtime code
