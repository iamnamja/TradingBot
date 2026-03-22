# Task 049a — Run Task Export and Wrapper Dedupe

## Goal

Remove duplicate public wrapper/export definitions from `agents/run_task.py` without changing external behavior.

The current shell is functionally strong, but still contains duplicate definitions for key compatibility surfaces. This task is specifically about convergence and deduplication, not new behavior.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `tests/test_run_task_shell_parity.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_run_task_shell_convergence.py`
- `README.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=default_provider
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=run_checks
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=_spec_mode_exports

## Critical compatibility requirement

Do not weaken or remove the already-merged shell seams from tasks 043–048.

In particular, keep these seams present and behaviorally compatible:

- `_artifact_quarantine_exports()`
- `_spec_mode_exports()`
- `_failure_journal_exports()`
- `_bootstrap_exports()`
- `run_checks()`

## Required behavior

1. `agents/run_task.py` should contain only **one active definition** for each of:
   - `default_provider`
   - `run_checks`
   - `_spec_mode_exports`
2. current runtime-foundations, shell-parity, and spec/execution behavior must remain green
3. add a deterministic test that asserts the shell no longer contains duplicate definitions for those public surfaces

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `tests/test_run_task_shell_convergence.py` proves there is one active definition per targeted public shell seam
- no already-merged 043–048 shell surface is removed or renamed
