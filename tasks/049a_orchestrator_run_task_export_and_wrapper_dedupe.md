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

## Harness policy

- FILE: tests/test_run_task_shell_parity.py MODE=TESTS_ONLY
- FILE: tests/test_run_task_runtime_foundations.py MODE=TESTS_ONLY
- FILE: tests/test_run_task_shell_convergence.py MODE=TESTS_ONLY

## Critical compatibility requirement

Do not weaken or remove the already-merged shell seams from tasks 043–048.

In particular, keep these seams present and behaviorally compatible:

- `_artifact_quarantine_exports()`
- `_spec_mode_exports()`
- `_failure_journal_exports()`
- `_bootstrap_exports()`
- `run_checks()`

## Task-shape guidance

This task intentionally does **not** put `agents/run_task.py` under protected method-replacement mode.

The dedupe work crosses duplicated definitions and surrounding shared shell lines, so `agents/run_task.py` should be handled as a normal surgical full-file patch in this task.

Do **not** use this task to redesign the shell or move major routing logic out of the file. That belongs to `049b`.

## Required behavior

1. `agents/run_task.py` should contain only **one active definition** for each of:
   - `default_provider`
   - `run_checks`
   - `_spec_mode_exports`
2. current runtime-foundations, shell-parity, and spec/execution behavior must remain green
3. add a deterministic test that asserts the shell no longer contains duplicate definitions for those public surfaces
4. do not rename, remove, or relocate the public shell seams stabilized in 043–048

## Failure classification guidance

- if the work fails because protected method mode cannot remove duplicate definitions across the file, that is a **task-shape failure**, not a product failure
- if the dedupe patch lands but compatibility tests fail, that is a **shell/code failure** and should be fixed directly rather than retried blindly

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `tests/test_run_task_shell_convergence.py` proves there is one active definition per targeted public shell seam
- no already-merged 043–048 shell surface is removed or renamed
