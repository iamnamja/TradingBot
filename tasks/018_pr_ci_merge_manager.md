# Task 018: PR / CI / merge manager

## Goal
Automate PR creation, CI polling, merge decisions, and post-merge sync for the orchestrator.

## Deliverables
- `src/builder/orchestrator/merge.py`
  - `class MergeManager`
  - methods for:
    - create_pr
    - wait_for_ci or poll_ci
    - merge_pr
    - sync_main

- `tests/test_merge_manager.py`

## Required behavior
### Scope
For v1, implement a command-wrapper abstraction that can be mocked in tests.
Do not require live GitHub API calls in unit tests.

### Required operations
Support:
- creating a PR
- checking CI result
- merging when policy allows
- syncing local main after merge

### Safety
Do not allow merge if:
- CI failed
- review checker says not mergeable
- approval is required but missing

## Portability requirement
Do not hardcode TradingBot repo names.
Allow repo/branch names to be passed in.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- tests do not require live GitHub connectivity
