# Task 053 — Orchestrator Stable Seam Registry

## Goal

Create an explicit, stable seam registry for orchestrator integration tests so future tasks and tests stop guessing private/internal names such as ad hoc `run_task.*` globals.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `tests/test_run_task_shell_convergence.py`
- `tests/test_orchestrator_public_surface.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=_shell_router_exports MAX_CHANGED_LINES=60
- FILE: agents/lib/shell_router.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ANCHOR_BEFORE="def route_shell_main(" ALLOW_NEW_METHOD=build_shell_seam_registry MAX_CHANGED_LINES=120
- FILE: agents/lib/shell_router.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ANCHOR_BEFORE="def route_shell_main(" ALLOW_NEW_METHOD=shell_seam_exports MAX_CHANGED_LINES=160
- FILE: tests/test_run_task_shell_convergence.py MODE=TESTS_ONLY
- FILE: tests/test_orchestrator_public_surface.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY

## Required behavior

1. define a small stable seam registry for orchestrator integration tests
2. expose the seam registry through stable helper(s), not scattered ad hoc globals
3. ensure tests can patch model invocation, validator invocation, failure-journal access, and review/quarantine access through those stable seams
4. document the supported seam names and intended use

## Suggested seam coverage

The registry should cover current live seam families such as:

- model/bundle request invocation
- validator/check invocation
- failure-journal exports
- review / quarantine exports

The implementation does not need to expose raw internal modules if that is not the current live pattern; it only needs to expose stable test seams.

## Critical implementation constraint

This task must avoid destructive whole-file rewrites of critical core files.

In particular:

- do not replace `agents/run_task.py` wholesale
- do not replace `agents/lib/shell_router.py` wholesale
- only modify:
  - `agents.run_task._shell_router_exports`
  - append new helper functions in `agents/lib/shell_router.py` before `def route_shell_main(`
- preserve the current module header / imports / entrypoint structure
- do not rewrite the protected header/docstring regions of critical core files

## Stable seam shape

Prefer a seam registry that returns stable family names and export helper names, for example:

- `bootstrap`
- `spec_mode`
- `failure_journal`
- `validator_runner`
- `artifact_quarantine`
- `runtime_foundations`
- `parser_policy`
- `semantic_preflight`
- `shell_router`

A helper such as `build_shell_seam_registry()` may return the canonical mapping, and `shell_seam_exports()` may return the same mapping or a read-only view.

## Critical file-shape guardrails

This task must **not** corrupt the file-bundle transport by embedding raw bundle markers inside file contents.

In particular:

- do **not** place literal standalone lines such as:
  - `BEGIN_FILE_BUNDLE`
  - `FILE: ...`
  - `END_FILE`
  - `END_FILE_BUNDLE`
  inside Python docstrings, markdown examples, or any generated file contents
- if tests or docs need to mention bundle markers, render them inline or split the token, for example `FI` + `LE:`
- do not introduce a placeholder path such as `path/relative/to/repo.py` as a real repo file in the bundle
- do not emit malformed or truncated triple-quoted strings

## Compatibility constraints

- preserve the public CLI shell and `route_shell_main(...)` behavior
- do not break post-050/052 bootstrap compatibility surfaces
- keep existing shell-router/export tests green
- do not redesign provider behavior or repo checks in this task

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- orchestrator integration tests can rely on stable seam names instead of guessing private globals
- docs describe the stable seam registry and what is supported for monkeypatching
- generated file contents do not contain malformed bundle-marker examples that break Python syntax
