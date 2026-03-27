# Task 054a — Orchestrator Meta Harness Lane Gate

## Goal

Harden the deterministic lane gate that blocks **normal full-file bundle editing**
for core meta harness files, while preserving the current live public surface.

This task is intentionally narrow. It should refine the existing
`enforce_meta_file_task_gate` behavior in place rather than broadening the task
into general preflight or bundle parsing work.

## Deliverables

Create or update these exact files. Every listed file must appear in the task result:

- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_orchestrator_public_surface.py`

Do **not** modify any other files in this task.

## Harness policy

- FILE: `agents/run_task.py` MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=`enforce_meta_file_task_gate` MAX_CHANGED_LINES=180
- FILE: `tests/test_run_task_runtime_foundations.py` MODE=TESTS_ONLY
- FILE: `tests/test_orchestrator_public_surface.py` MODE=TESTS_ONLY

## Required behavior

Refine `enforce_meta_file_task_gate` so that it remains:

- deterministic
- narrow
- actionable
- aligned to the current live meta harness file set

The helper must continue to reject the **normal file-bundle lane** for core meta
harness files such as:

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `agents/lib/bundle_parser.py`
- `agents/lib/protected_file_policy.py`

The helper should also reject suspicious multi-meta-file normal-bundle targets.

The response text should be short and actionable.

## Critical guardrails

This task must be **surgical**.

Do **not** use this task to:

- modify `request_and_parse_bundle`
- redesign protected-method transport
- rewrite parser/policy helpers
- add new seam families
- move docs or rename public helpers

Preserve the live helper name exactly as:

- `enforce_meta_file_task_gate`

If the helper already exists, refine it in place. Do **not** add a duplicate
second definition.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is green
- `enforce_meta_file_task_gate` remains callable on `agents.run_task`
- normal full-file bundle attempts against core meta harness files are rejected deterministically
- the change remains within the protected replace-method policy for this helper
