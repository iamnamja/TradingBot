# Task 038d — Import Symbol Preflight for Agent Bundles

## Goal

Extend the existing `validate_imports(...)` preflight in `agents/run_task.py` so invalid repo-local imported symbols are rejected before `pytest`.

## Why

Task 039 repeatedly failed because generated test bundles imported names like `BacklogStore` / `TaskRecord` from real repo modules even when those symbols did not exist. The current harness already validates repo-local module existence, but it does not yet validate imported symbol existence.

This task should harden that preflight without broad rewrites to the task runner.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=validate_imports MAX_CHANGED_LINES=260
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
- workspace restore behavior
- virtual protected-file context behavior
- current missing-module validation behavior except to extend it with repo-local symbol validation

All existing passing tests must continue to pass.

## Required implementation shape

For `agents/run_task.py`:

- Do not rewrite the full file.
- Use the protected replace-method flow only.
- Replace the existing top-level function named `validate_imports`.
- Do not add a second `validate_imports` definition.
- The protected response payload must contain exactly one top-level function and nothing else.
- Do not add any additional top-level defs.
- Do not add any additional top-level classes.
- Do not add any additional top-level constants.
- Do not add helper functions at module scope.
- Do not define nested helper functions inside `validate_imports(...)`.
- Do not use any additional `def` statements anywhere inside the replacement method text.
- Keep helper logic inline using local variables, loops, comprehensions, and existing stdlib calls only.
- For the protected method response, return only the method insertion payload requested by the harness. Do not emit a normal `BEGIN_FILE_BUNDLE` response for `agents/run_task.py`.

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
- appending a new `validate_imports` instead of replacing the existing one
- emitting multiple top-level methods in the protected response payload
- using nested helper defs inside `validate_imports`
- adding helper methods like `module_to_paths`, `module_exists_local`, `module_source_exists`, `load_module_exports`, `_repo_local_roots`, `_repo_local_module_path`, `_load_module_exports`, `_module_spec`, `_package_exports`, `_is_repo_local`, etc. at top level
- adding extra `def` statements anywhere in the replacement `validate_imports` payload
- changing provider/model defaults
- changing protected-file baseline logic
- touching orchestrator production files
- touching TradingBot production files
- importing nonexistent repo-local symbols in the new tests
- relying on external services in tests

## Test requirements

`tests/test_run_task_import_validation.py` must be self-contained and deterministic.

Do not depend on whatever symbols currently exist in real repo modules like `builder.orchestrator.backlog`.

Instead, build bundles in the tests that include their own repo-local module files under `src/tradingbot/...` or `src/builder/...` and validate imports against those bundled files.

Cover at least:

1. valid repo-local symbol import passes using a bundled module file
2. missing module fails
3. existing module but missing imported symbol fails using a bundled module file
4. alias import of an existing symbol passes
5. star import is ignored/passes
6. bundled module symbol definitions are recognized without writing to disk first
7. package `__init__.py` exports are recognized when present in the bundle

Tests must be Windows-portable and self-contained.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- invalid repo-local symbol imports are blocked before `pytest`
- `agents/run_task.py` changes are limited to one protected method replacement
