# Task 039b — Protected API Semantic Preflight

## Goal

Extend the existing `validate_static_bundle_contracts(...)` preflight in `agents/run_task.py` so the harness rejects obvious semantic/API mismatches against protected Python files before spending an iteration on `ruff` / `pytest`.

## Why

The harness already catches syntax, bundle completeness, deliverable scope, and some static contract regressions. It still does not validate enough about the real protected API surface.

Recent failures showed these examples:

- tests importing or calling symbols that do not exist on protected modules/classes
- tests calling nonexistent methods like `runner.run()` / `runner.run_all_tasks()`
- tests constructing `OrchestratorRunner` with the wrong config object shape, even though the real constructor requires either a `ProjectConfig` or an object exposing `.config`

This task comes after 039a so it can rely on the hardened protected method replacement path.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=validate_static_bundle_contracts MAX_CHANGED_LINES=420
- `tests/test_run_task_protected_api_semantic_preflight.py`

Both listed files must be materially updated.

## Harness policy

- FILE: tests/test_orchestrator_end_to_end.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

All existing public APIs and harness behavior in `agents/run_task.py` must remain backward compatible.

Do not change:
- provider/model selection behavior
- retry loop behavior
- bundle parsing rules
- protected-file policy enforcement
- workspace restore behavior
- branch / git behavior
- import validation behavior outside the targeted semantic extension
- TradingBot or orchestrator production code under `src/`

All existing passing tests must continue to pass.

## Required implementation shape

For `agents/run_task.py`:

- Do not rewrite the full file.
- Use the protected replace-method flow only.
- Replace exactly one existing top-level function named `validate_static_bundle_contracts`.
- The method replacement payload must contain exactly one top-level function and nothing else.
- Do not add any additional top-level defs.
- Do not add any additional top-level classes.
- Do not add any additional top-level constants.
- Do not define nested helper functions inside `validate_static_bundle_contracts(...)`.
- Do not use any additional `def` statements anywhere inside the replacement method text.
- Keep helper logic inline using local variables, loops, comprehensions, `ast`, and existing stdlib calls only.
- For the protected method response, return only the method insertion bundle requested by the harness. Do not emit a normal `BEGIN_FILE_BUNDLE` response for `agents/run_task.py`.

### Required method signature

```python
def validate_static_bundle_contracts(bundle: Dict[str, str], task_text: str) -> Tuple[bool, str]:
```

The replacement method must preserve all current passing static contract checks and extend them with the semantic/API checks described below.

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

### Success contract

Do not change the existing success contract of `validate_static_bundle_contracts(...)`.

If the current baseline returns `(True, "")` on success, keep that behavior.
Do not change it to `(True, "ok")` just for new tests.

### Test import surface

The tests in `tests/test_run_task_protected_api_semantic_preflight.py` must use normal package imports, not `src.`-prefixed imports.

Use imports like:

- `from builder.orchestrator.runner import OrchestratorRunner`
- `from builder.orchestrator.project_config import ProjectConfig`

Do NOT use:

- `from src.builder.orchestrator.runner import ...`
- `from src.builder.orchestrator.project_config import ...`

### Failure messaging

When the validator blocks a bundle, the error must be actionable. Examples:

- `tests/test_x.py: OrchestratorRunner() is called with 0 args but protected constructor requires 3`
- `tests/test_x.py: variable 'runner' is an OrchestratorRunner; protected API has no method 'run_all_tasks'`
- `tests/test_x.py: OrchestratorRunner first arg must be ProjectConfig or object with .config`

## Exact forbidden patterns

- rewriting all of `agents/run_task.py`
- emitting multiple top-level methods in the protected replacement payload
- adding helper methods/functions at top level
- adding extra `def` statements anywhere inside the replacement payload
- modifying any file under `src/`
- changing import/module validation behavior unrelated to the targeted semantic extension
- relying on external services in tests
- using `src.`-prefixed imports in the new test file
- asserting that success returns the literal message `"ok"` unless the current baseline already does that

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
- `agents/run_task.py` changes are limited to one protected method replacement
