# Task 039a — Protected API Semantic Preflight

## Goal

Teach `agents/run_task.py` to reject obvious semantic/API mismatches against protected Python files before spending an iteration on `ruff` / `pytest`.

## Why

The harness already catches syntax, bundle completeness, deliverable scope, and some static contract regressions. It still does not validate enough about the real protected API surface.

Recent failures showed these examples:

- tests importing or calling symbols that do not exist on protected modules/classes
- tests calling nonexistent methods like `runner.run()` / `runner.run_all_tasks()`
- tests constructing `OrchestratorRunner` with the wrong config object shape, even though the real constructor requires either a `ProjectConfig` or an object exposing `.config`

This task adds a lightweight semantic preflight layer for protected Python APIs.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `tests/test_run_task_protected_api_semantic_preflight.py`

Both listed files must be materially updated.

## Scope

Keep the change narrowly focused on preflight validation in the harness.

Do not change:
- provider/model selection behavior
- retry loop behavior
- bundle parsing rules
- protected-file policy enforcement
- workspace restore behavior
- branch / git behavior
- TradingBot or orchestrator production code under `src/`

## Required behavior

Add a protected-Python semantic preflight that can inspect real protected files on disk and reject generated code when the mismatch is statically obvious.

### Minimum required detections

At minimum, the preflight must reject these patterns when the bundle references protected orchestrator Python files:

1. importing a symbol from a protected module when that symbol does not exist
2. calling a method on an imported protected class or obvious instance variable when that method does not exist
3. constructing a protected class with an obviously wrong argument count
4. constructing `OrchestratorRunner` with a bare config-like object that lacks `.config` when the current protected constructor requires it
5. calling `runner.run()` or `runner.run_all_tasks()` when only `run_next_task()` and `run_loop()` exist

### Validation style

Keep the validator lightweight and deterministic.

It should use:
- Python AST parsing
- protected file contents from disk
- real symbol/method names discovered from those files
- simple dataflow only where the variable binding is obvious in the same file

It should NOT try to build a full static type checker.

### Failure messaging

When the validator blocks a bundle, the error must be actionable. Examples:

- `tests/test_x.py: OrchestratorRunner() is called with 0 args but protected constructor requires 3`
- `tests/test_x.py: variable 'runner' is an OrchestratorRunner; protected API has no method 'run_all_tasks'`
- `tests/test_x.py: OrchestratorRunner first arg must be ProjectConfig or object with .config`

## Tests

`tests/test_run_task_protected_api_semantic_preflight.py` must include deterministic tests for at least:

1. valid protected constructor usage passes
2. zero-arg `OrchestratorRunner()` is rejected
3. missing protected method call is rejected
4. missing protected import symbol is rejected
5. bare `SimpleNamespace(...)` as first arg to `OrchestratorRunner` is rejected when `.config` is required
6. non-protected modules are ignored by this validator

Tests must be Windows-portable and must not call external services.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- semantic protected API drift is blocked before full test execution
