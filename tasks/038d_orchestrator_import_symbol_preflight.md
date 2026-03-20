# Task 038d — Import Symbol Preflight for Agent Bundles

## Goal

Harden `agents/run_task.py` so it rejects agent-generated bundles that import non-existent repo-local symbols before spending an iteration on `pytest`.

## Why

Task 039 repeatedly failed because generated tests imported names like `BacklogStore` or `TaskRecord` from repo-local modules where those symbols do not exist. The current harness validates module-path existence only, not imported symbol existence.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=validate_imports MAX_CHANGED_LINES=260
- `tests/test_run_task_import_validation.py`

Both listed files must be materially updated in the same bundle.

## Harness policy

- FILE: tests/test_orchestrator_end_to_end.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

All existing public APIs and protected-file behavior in `agents/run_task.py` must remain backward compatible.

Do not change:
- provider/model selection behavior
- retry loop behavior
- protected-file policy enforcement
- append/replace method application behavior outside this specific `validate_imports` replacement
- workspace restore behavior
- virtual protected-file context behavior
- current missing-module validation behavior except to extend it with repo-local symbol validation

All existing passing tests must continue to pass.

## Required implementation shape

For `agents/run_task.py`:

- Do not rewrite the full file.
- Use the protected single-method replacement flow only.
- Replace the existing top-level function named `validate_imports`.
- The replacement payload must contain exactly one top-level function and nothing else.
- Do not add any additional top-level defs.
- Do not add any additional top-level classes.
- Do not add any additional top-level constants.
- Do not add helper functions at module scope.
- Do not define nested helper functions inside `validate_imports(...)`.
- Do not use any additional `def` statements anywhere inside the replacement method text.
- Keep helper logic inline using local variables, loops, comprehensions, and existing stdlib calls only.
- For the protected replacement response, return only the method insertion payload requested by the harness. Do not emit a normal `BEGIN_FILE_BUNDLE` response for `agents/run_task.py`.

### Required method signature

```python
def validate_imports(bundle: Dict[str, str]) -> Tuple[bool, str]:
```

The replacement `validate_imports(...)` method must preserve the current missing-module validation semantics and extend them with repo-local imported-symbol validation.

## Required behavior

Inspect Python imports of these forms when they target repo-local packages:

- `from builder.orchestrator.some_module import Name`
- `from tradingbot.some_module import Name`

For repo-local imports only:

- fail validation if the target module does not exist
- fail validation if an imported symbol does not exist in the target module or package export surface
- allow `as` aliases
- allow importing submodules that actually exist
- allow `*` imports to pass unchanged
- ignore third-party imports

The validation must work against:
- files that already exist in the repo
- files included in the current bundle
- package `__init__.py` exports where applicable

## Test requirements

`tests/test_run_task_import_validation.py` must be deterministic and self-contained.

Do not assume any specific symbol already exists in the real repository under `src/builder/orchestrator/backlog.py`.

Instead, the tests should create minimal temporary repo-local package files under `tmp_path`, `monkeypatch.chdir(tmp_path)`, and verify `validate_imports(...)` against those temporary files.

Cover at least:

1. valid repo-local symbol import passes
2. missing module fails
3. existing module but missing imported symbol fails
4. alias import of an existing symbol passes
5. star import is ignored/passes
6. bundled module symbol definitions are recognized without writing to disk first
7. package `__all__` exports are honored

Tests must be Windows-portable and must not call external services.

## Exact error messaging

When symbol validation fails, surface a clear message like:

- `tests/test_x.py: imports missing symbol 'BacklogStore' from 'builder.orchestrator.backlog'`

When module validation fails, preserve the existing missing-module message format.

## Retry behavior

This must participate in the existing pre-write validation flow the same way current import validation does:

- reject before files are written
- append actionable feedback into the task text
- stop early on repeated violations using the existing policy-block limit pattern

## Exact forbidden patterns

- rewriting all of `agents/run_task.py`
- emitting multiple top-level methods in the protected replacement payload
- using nested helper defs inside `validate_imports`
- adding helper methods like `module_to_paths`, `module_exists_local`, `load_module_exports`, `module_source_exists`, `load_module_texts`, `_module_spec`, `_package_exports`, `_is_repo_local`, etc.
- adding extra `def` statements anywhere in the replacement `validate_imports` payload
- changing provider/model defaults
- changing protected-file baseline logic
- touching orchestrator production files
- touching TradingBot production files
- importing nonexistent repo-local symbols in the new tests
- relying on external services in tests

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- invalid repo-local symbol imports are blocked before `pytest`
- `agents/run_task.py` changes are limited to one surgical replacement of `validate_imports`
