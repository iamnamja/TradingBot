# Task 039a — Protected Method Edit Engine (Tests Only)

## Goal

Add deterministic tests for the current protected method edit engine behavior in `agents/run_task.py` without changing production code.

## Why

We are pausing production changes to the harness so we can validate the current protected method edit engine before continuing the hardening tranche.

This task must verify the existing append-method and replace-method behavior already present in `agents/run_task.py`.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_run_task_protected_method_edit_engine.py`

The listed file must be materially updated.

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

This task adds tests only.

It must not change:
- `agents/run_task.py`
- provider/model selection behavior
- bundle parsing behavior
- git / branch behavior
- any file under `src/`

All existing passing tests must continue to pass.

## Current baseline under test

The tests must validate the current protected method edit engine already implemented in `agents/run_task.py`, including real functions such as:

- `parse_harness_file_policies(...)`
- `_extract_protected_method_targets(...)`
- `apply_method_insertion(...)`
- `apply_method_replacement(...)`
- `parse_method_insertion_bundle(...)`
- `request_and_parse_method_insertion(...)`

Only import symbols that actually exist on the current baseline.

## Required test scenarios

Add deterministic tests covering at least:

1. append target extraction from a real task snippet using `MODE=EXACT_COPY_PLUS_APPEND_METHOD`
2. replace target extraction from a real task snippet using `MODE=EXACT_COPY_PLUS_REPLACE_METHOD`
3. append method application into baseline content before an anchor
4. replace method application for an existing method in baseline content
5. duplicate-method payload rejection
6. missing replacement target rejection
7. missing append anchor rejection
8. malformed protected payload parsing failure for method insertion bundles

## Test construction rules

- Use normal imports from `agents.run_task`
- Do not mock the entire module
- For payload tests, use synthetic baseline strings and synthetic bundle text
- Keep tests Windows-portable and self-contained
- Do not call external services
- Do not modify repo files during the tests

### CRITICAL bundle-string construction rule

Because the outer agent harness parses `FILE:` / `END_FILE` markers literally, the generated test file must NOT contain a triple-quoted source fixture with literal lines that begin with:

- `FILE:`
- `END_FILE`
- `BEGIN_FILE_BUNDLE`
- `END_FILE_BUNDLE`

inside the emitted file contents.

Instead, when constructing synthetic bundle text inside the test file, build those markers indirectly, for example:
- with `"FI" "LE:"` string splitting
- or with `"BEGIN_" + "FILE_BUNDLE"`
- or with `"
".join([...])`

so the final runtime string is correct, but the emitted source file does not contain literal bundle-marker lines that confuse the outer parser.

## Exact forbidden patterns

- modifying `agents/run_task.py`
- creating `tests/test_run_task_protected_api_semantic_preflight.py`
- replacing or focusing on `validate_static_bundle_contracts(...)`
- solving semantic/API preflight instead of protected method edit engine
- modifying any file under `src/`
- using triple-quoted fixtures that contain literal line-start bundle markers like `FILE:` or `END_FILE`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- the current protected method edit engine is covered by deterministic tests without production edits
