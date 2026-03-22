# Task 044a — Spec Mode Capture

## Goal

Add a spec-generation mode that captures clarifications, forbidden patterns, acceptance criteria, verification commands, and expected outputs into a frozen task artifact.

The implementation should continue shrinking `agents/run_task.py` by moving spec-mode logic into `agents/lib/spec_mode.py`.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/spec_mode.py`
- `agents/run_task.py`
- `tests/test_spec_mode_capture.py`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=main
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_spec_mode_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Critical compatibility requirement

This task must preserve the current shell contract unless a new spec-mode path is added **additively**.

Do not replace the current positional `task` argument or existing flags. If spec mode is exposed through CLI, it must be additive and must not break current execution-mode behavior.

The goal is:
- `agents/lib/spec_mode.py` owns spec-mode logic
- `agents/run_task.py` remains thin orchestration glue

## Current shell / CLI guidance

Tests must validate the **current** shell surface that exists in `agents/run_task.py`.

Specifically:

- Do **not** assume `main(argv)` if the current shell exposes `main()` reading from `sys.argv`
- Do **not** assume legacy flags like `--task` or `--non-interactive` unless they actually exist
- If invoking `main()`, monkeypatch `sys.argv` and use the current positional `task` plus existing optional flags only
- Do **not** invent helper names unless they actually exist in the current shell or are explicitly added by this task

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

do **not** place those raw marker strings at the start of a source line inside generated file content.

Instead, encode them safely using split string tokens or concatenation, for example:

- `"FI" + "LE: sample.py\n"`
- `"END_" + "FILE\n"`
- `"BEGIN_" + "FILE_BUNDLE"`

## Required behavior

Spec mode should:

- identify when the task is underspecified
- produce a structured frozen spec artifact
- capture:
  - scope
  - edge cases
  - forbidden patterns
  - acceptance criteria
  - verification commands
  - expected outputs when available

This mode should not perform implementation work.

## Test requirements

Add deterministic tests that validate:

1. underspecified task inputs are converted into a structured frozen spec artifact
2. the frozen artifact is deterministic enough to be reused by execution mode
3. spec mode logic lives primarily in `agents.lib.spec_mode`
4. `agents.run_task.main()` only thinly routes into spec-mode behavior
5. current execution-mode behavior remains available after spec-mode support is added

Tests should validate stable artifact sections/fields, not overfit to incidental prose wording.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- a frozen spec artifact can be generated deterministically
- `agents/run_task.py` is thinner after delegating spec-mode logic
