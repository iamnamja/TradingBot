# Task 042b — Extract Parsers and Policies

## Goal

Extract bundle parsing, task-contract parsing, and protected-file policy handling into reusable modules, with no behavior change.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/bundle_parser.py`
- `agents/lib/task_contracts.py`
- `agents/lib/protected_file_policy.py`
- `agents/run_task.py`
- `tests/test_run_task_parsers_and_policies.py`

All listed files must be materially updated in the same bundle.

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

This is a no-behavior-change extraction task.

All current behavior around:

- file-bundle parsing
- method-insertion bundle parsing
- task contract directives
- protected-file modes
- required deliverable enforcement

must remain behaviorally identical.

## Required extraction targets

### `bundle_parser.py`

Move logic for:
- normal file bundle parsing
- method insertion bundle parsing
- malformed bundle detection
- nested `FILE:` / `END_FILE` validation

### `task_contracts.py`

Move logic for:
- machine-readable directive parsing
- constructor/method/result contract parsing
- directive normalization

### `protected_file_policy.py`

Move logic for:
- harness file policy parsing
- protected append/replace target extraction
- protected-file mode normalization
- protected-file violation reporting helpers

## Test requirements

Add deterministic tests for:

1. normal file-bundle parsing parity
2. malformed file-bundle rejection parity
3. method insertion parsing parity
4. contract directive parsing parity
5. protected-file policy parsing parity
6. append/replace target extraction parity

## Exact forbidden patterns

- behavior changes disguised as refactor
- touching orchestrator engine files under `src/builder/orchestrator/`
- removing existing public helper functions from `run_task.py` unless they remain import-compatible or are clearly delegated wrappers
- relaxing protected-file enforcement

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- parser/policy logic is modularized
- current behavior is preserved exactly on covered cases
