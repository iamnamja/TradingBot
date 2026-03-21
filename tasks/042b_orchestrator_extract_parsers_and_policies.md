# Task 042b — Extract Parsers and Policies

## Goal

Extract bundle parsing, task-contract parsing, and protected-file policy handling into reusable modules, with no behavior change.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/bundle_parser.py`
- `agents/lib/task_contracts.py`
- `agents/lib/protected_file_policy.py`
- `agents/run_task.py`
- `tests/test_run_task_parsers_and_policies.py`

All listed files must be materially updated in the same bundle.

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=_deliverables_section
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=parse_file_bundle
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=parse_method_insertion_bundle
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=parse_task_contract_directives
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=parse_harness_file_policies
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=_extract_protected_method_targets
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_parser_policy_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Critical compatibility requirement

This is a no-behavior-change extraction task.

All current behavior around:

- file-bundle parsing
- method-insertion bundle parsing
- task contract directives
- protected-file modes
- required deliverable enforcement

must remain behaviorally identical.

## Required extraction targets

### `bundle_parser.py`

Move logic for:
- normal file bundle parsing
- method insertion bundle parsing
- malformed bundle detection
- nested `FILE:` / `END_FILE` validation

### `task_contracts.py`

Move logic for:
- machine-readable directive parsing
- constructor/method/result contract parsing
- directive normalization

### `protected_file_policy.py`

Move logic for:
- harness file policy parsing
- protected append/replace target extraction
- protected-file mode normalization
- protected-file violation reporting helpers

## Required implementation shape

`agents/run_task.py` must remain the public entrypoint, but the methods listed in the harness policy should become thin delegating wrappers over the extracted modules.

Do NOT emit a normal full-file `FILE: agents/run_task.py` bundle for the protected file. Protected-file edits for `agents/run_task.py` must be satisfied only through the declared method replacement / append-method policy.

Do NOT relax protected-file enforcement to make the extraction easier.

## Bundle transport safety requirement

This task is transmitted through the runner's file-bundle protocol.

When generated source or tests need to refer to literal bundle markers such as:

- `BEGIN_FILE_BUNDLE`
- `FILE:`
- `END_FILE`
- `END_FILE_BUNDLE`
- `BEGIN_METHOD_INSERTION`
- `BEGIN_METHOD`
- `END_METHOD`
- `END_METHOD_INSERTION`

do NOT place those raw marker strings at the start of a source line inside the generated file content.

Instead, encode them safely using split string tokens or concatenation, for example:

- `"FI" + "LE: sample.py\n"`
- `"END_" + "FILE\n"`
- `"BEGIN_" + "FILE_BUNDLE"`

This is required so the bundle transport cannot misparse generated test/source content as outer bundle structure.

## Test requirements

Add deterministic tests for:

1. normal file-bundle parsing parity
2. malformed file-bundle rejection parity
3. method insertion parsing parity
4. contract directive parsing parity
5. protected-file policy parsing parity
6. append/replace target extraction parity

## Exact forbidden patterns

- behavior changes disguised as refactor
- touching orchestrator engine files under `src/builder/orchestrator/`
- removing existing public helper functions from `run_task.py` unless they remain import-compatible or are clearly delegated wrappers
- relaxing protected-file enforcement
- broad rewrite of `agents/run_task.py`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- parser/policy logic is modularized
- current behavior is preserved exactly on covered cases
