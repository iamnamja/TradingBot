# Task 042c — Extract Semantic Preflight

## Goal

Extract static contract enforcement and semantic preflight logic into a dedicated module, with no behavior change.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/semantic_preflight.py`
- `agents/run_task.py`
- `tests/test_run_task_semantic_preflight_parity.py`

All listed files must be materially updated in the same bundle.

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

This is a no-behavior-change extraction task.

The following behavior must remain intact:

- protected API import validation
- obvious constructor misuse detection
- forbidden import/call enforcement from machine-readable directives
- result-key contract enforcement
- current compatibility with monkeypatched helper shapes used by tests

## Required extraction targets

Move into `semantic_preflight.py`:

- static bundle contract validation
- protected Python semantic issue detection
- helper functions for module/source/export inspection used by semantic validation

`agents/run_task.py` may delegate to the new module but must preserve the current public behavior.

## Test requirements

Add deterministic parity tests for:

1. valid protected constructor usage
2. zero-arg constructor rejection
3. missing protected method call rejection
4. missing protected import symbol rejection
5. config-wrapper misuse rejection
6. non-protected code being ignored
7. compatibility with current monkeypatch styles used in semantic tests

## Exact forbidden patterns

- behavior changes to semantic policy
- weakening contract enforcement to get tests green
- touching orchestrator engine files under `src/builder/orchestrator/`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- semantic preflight is modularized
- current behavior is preserved on the covered baseline
