# Task 038d — Import Symbol Preflight for Agent Bundles

## Goal

Harden `agents/run_task.py` so it rejects agent-generated bundles that import non-existent symbols from existing repo modules before spending an iteration on `pytest`.

## Why

Task 039 repeatedly failed because the generated test file imported names like `BacklogStore` / `TaskRecord` from `builder.orchestrator.backlog`, even though the module exists but those symbols do not. The current harness import validation checks module existence only, not imported symbol existence.

This is a narrow harness gap and is worth fixing before rerunning Task 039.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ANCHOR_BEFORE=missing_module_hints( ALLOW_NEW_METHOD=validate_imports MAX_CHANGED_LINES=160
- `tests/test_run_task_import_validation.py`

Both listed files must be materially updated.

## Scope

Keep the change as small as possible.

Do not modify orchestrator production files.
Do not modify TradingBot production files.
Do not change provider/model selection behavior.
Do not weaken existing protected-file policy enforcement.

For `agents/run_task.py`:

- Do not rewrite the full file.
- Add exactly one new top-level function named `validate_imports`.
- Place it immediately before `def missing_module_hints(` using the protected append-method flow.
- Preserve the existing missing-module validation behavior and extend it with repo-local imported-symbol validation.
- Any small helper logic needed for symbol inspection should live inside `validate_imports` as nested helper logic, not as additional top-level functions.

## Required behavior

### New static validation

Add bundle validation that inspects Python imports of these forms:

- `from builder.orchestrator.some_module import Name`
- `from tradingbot.some_module import Name`

For imports that target repo-local modules/packages:

- fail validation if the target module does not exist
- fail validation if an imported symbol does not exist in the target module/package
- allow `as` aliases
- allow importing submodules that actually exist
- allow `*` imports to pass unchanged
- ignore third-party imports

The validation should work against:
- files that already exist in the repo
- files included in the current bundle
- package `__init__.py` exports where applicable

### Error messaging

When symbol validation fails, the harness should surface a clear message like:

- `tests/test_x.py: imports missing symbol 'BacklogStore' from 'builder.orchestrator.backlog'`

### Retry behavior

This should participate in the existing pre-write validation flow the same way current import validation does:
- reject before files are written
- append actionable feedback into the task text
- stop early on repeated violations using the existing policy-block limit pattern

## Tests

Add deterministic unit tests covering at least:

1. valid repo-local symbol import passes
2. missing module fails
3. existing module but missing imported symbol fails
4. alias import of an existing symbol passes
5. star import is ignored/passes
6. bundled module symbol definitions are recognized without writing to disk first

Tests must be Windows-portable and must not call external services.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- invalid repo-local symbol imports are blocked before `pytest`
