# Task 055 — Orchestrator Stable Seam Registry

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

## Critical file-shape guardrails

This task must **not** corrupt the file-bundle transport by embedding raw bundle markers inside file contents.

In particular:

- do **not** place literal standalone lines such as:
  - `BEGIN_FILE_BUNDLE`
  - `FILE: ...`
  - `END_FILE`
  - `END_FILE_BUNDLE`
  inside Python docstrings, markdown examples, or any generated file contents
- if `agents/run_task.py` is updated, preserve the existing top-of-file module docstring structure and avoid rewriting the file-bundle example block unless absolutely necessary
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
