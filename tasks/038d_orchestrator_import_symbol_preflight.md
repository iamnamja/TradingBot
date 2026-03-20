# Task 038d — Import Symbol Preflight for Agent Bundles

## Goal

Add repo-local imported-symbol validation to the existing `validate_imports(...)` preflight in `agents/run_task.py` so invalid agent bundles are rejected before `pytest`.

## Why

Task 039 repeatedly failed because the generated test bundle imported names like `BacklogStore` / `TaskRecord` from `builder.orchestrator.backlog`, even though the module exists but those symbols do not. The current harness already validates repo-local module existence, but it does not yet validate imported symbol existence.

This task is a narrow harness hardening task that should land before rerunning Task 039.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=validate_imports ANCHOR_BEFORE=missing_module_hints( MAX_CHANGED_LINES=260
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
- append-method insertion behavior
- workspace restore behavior
- virtual protected-file context behavior
- current missing-module validation behavior except to extend it with repo-local symbol validation

All existing passing tests must continue to pass.

## Required implementation shape

For `agents/run_task.py`:

- Do not rewrite the full file.
- Use the protected append-method flow only.
- Add exactly one new top-level function named `validate_imports`.
- Place it immediately before `def missing_module_hints(`.
- The insertion payload must contain exactly one top-level function and nothing else.
- Do not add any additional top-level defs.
- Do not add any additional top-level classes.
- Do not add any additional top-level constants.
- Do not add helper functions at module scope.
- Do not define nested helper functions inside `validate_imports(...)`.
- Do not use any additional `def` statements anywhere inside the inserted method text.
- Keep helper logic inline using local variables, loops, comprehensions, and existing stdlib calls only.
- For the protected insertion response, return only the method insertion payload requested by the harness. Do not emit a normal `BEGIN_FILE_BUNDLE` response for `agents/run_task.py`.

### Required method signature

```python
def validate_imports(bundle: Dict[str, str]) -> Tuple[bool, str]:
```

The inserted `validate_imports(...)` method must preserve the current module-existence validation semantics and extend them with repo-local imported-symbol validation.

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
- emitting multiple top-level methods in the protected insertion payload
- using nested helper defs inside `validate_imports`
- adding helper methods like `module_exists`, `resolve_module_source`, `symbol_exists`, `module_source_exists`, `_module_spec`, `_package_exports`, `_is_repo_local`, etc. at top level
- adding extra `def` statements anywhere in the inserted `validate_imports` payload
- changing provider/model defaults
- changing protected-file baseline logic
- changing append-method parsing behavior
- touching orchestrator production files
- touching TradingBot production files
- importing nonexistent repo-local symbols in the new tests
- relying on external services in tests

## Test requirements

`tests/test_run_task_import_validation.py` must cover at least:

1. valid repo-local symbol import passes
2. missing module fails
3. existing module but missing imported symbol fails
4. alias import of an existing symbol passes
5. star import is ignored/passes
6. bundled module symbol definitions are recognized without writing to disk first

Tests must be deterministic, Windows-portable, and self-contained.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- invalid repo-local symbol imports are blocked before `pytest`
- `agents/run_task.py` changes are limited to one additive protected-method insertion
