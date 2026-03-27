# Task 054b — Orchestrator Bundle Preflight / Localized Repair

## Goal

Refine `request_and_parse_bundle` so that the runner can catch common seam/task-shape
mistakes earlier and prefer **localized repair** when only a subset of generated
files is bad.

This task should improve resilience without redesigning the shell/runtime architecture.

## Deliverables

Create or update these exact files. Every listed file must appear in the task result:

- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`

Do **not** modify any other files in this task.

## Harness policy

- FILE: `agents/run_task.py` MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=`request_and_parse_bundle` MAX_CHANGED_LINES=520
- FILE: `tests/test_run_task_runtime_foundations.py` MODE=TESTS_ONLY

## Required behavior

Within `request_and_parse_bundle`, add or preserve lightweight preflight behavior
that can catch or explicitly report at least these mistake classes before a full
candidate bundle is accepted:

1. **Nonexistent seam names / monkeypatch targets**
   - detect references to seam names or monkeypatch targets that do not exist in the live repository contract
   - use the live seam/export surfaces as source of truth rather than invented aliases

2. **Recursive repo-wide validator invocation from generated tests**
   - detect integrated tests that appear to invoke real repo-wide `pytest -q` or `ruff check .`
   - this is specifically for accidental nested validation recursion, not normal in-process unit tests

3. **Task/deliverable scope drift**
   - generated files outside the task's listed deliverables should be flagged deterministically

4. **Suspicious miniature rewrite / stub collapse**
   - keep at least one conservative guard against replacing an existing nontrivial harness file with an obviously simplified stub or toy implementation
   - narrow/low-noise heuristics are acceptable, especially for `agents/run_task.py`

5. **Obvious Python text corruption indicators**
   - catch clearly suspicious code corruption indicators before full execution when practical

6. **Localized repair**
   - when a problem can be localized to one or a few generated files, prefer a targeted repair / retry rather than discarding all otherwise acceptable files

## Critical guardrails

This task must be **additive and safe**.

Do **not** use this task to:

- modify `enforce_meta_file_task_gate`
- rewrite `agents/run_task.py` wholesale
- redesign safe parallelism, failure journal, quarantine, or bootstrap behavior
- change the live shell-router public contract

Preserve the current live compatibility surface, including:

- `main`
- `build_messages`
- `request_and_parse_bundle`
- `run_checks`
- `validate_python_syntax`
- `_shell_router_exports()`
- `_failure_journal_exports()`

Do **not** rename the current failure-journal seam from `_report_failure`.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is green
- the shallow preflight catches at least the listed mistake classes before accepting a full bundle
- localized repair is preferred when only a subset of files is invalid or obviously corrupted
- the change remains within the protected replace-method policy for `request_and_parse_bundle`
