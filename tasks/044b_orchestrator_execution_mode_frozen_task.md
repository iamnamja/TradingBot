# Task 044b — Frozen Execution Mode

## Goal

Run the normal task execution workflow against a frozen spec artifact instead of an ambiguous raw task when spec mode has already been used.

The implementation should continue shrinking `agents/run_task.py` by moving frozen-task execution helpers into `agents/lib/spec_mode.py` (or a closely related helper surface introduced by 044a).

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/spec_mode.py`
- `agents/run_task.py`
- `tests/test_execution_mode_frozen_task.py`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=main
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_spec_mode_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Critical compatibility requirement

Execution mode must preserve the current shell contract unless frozen-spec support is added **additively**.

Do not replace the current positional `task` argument or existing flags.

The goal is:
- frozen-task execution behavior lives in helper/module code
- `agents/run_task.py` remains thin orchestration glue

## Current shell / CLI guidance

Tests must validate the **current** shell surface that exists in `agents/run_task.py`.

Specifically:

- Do **not** assume `main(argv)` if the current shell exposes `main()` reading from `sys.argv`
- Do **not** assume legacy flags like `--task` or `--non-interactive` unless they actually exist
- If invoking `main()`, monkeypatch `sys.argv` and use the current positional `task` plus existing optional flags only
- Do **not** invent nonexistent shell helper names

## Bundle transport safety requirement

This task is transmitted through the runner's file-bundle protocol.

If generated tests need to refer to literal bundle markers or frozen-task snippets that contain them, do **not** place raw marker strings such as `FILE:` or `END_FILE` at the start of a source line inside generated test content.

Use split tokens or concatenation instead.

## Required behavior

Execution mode should:

- accept a frozen spec artifact as the canonical task input
- preserve current execution behavior once the task is frozen
- keep the distinction between planning/spec work and implementation work visible in logs/audit

## Test requirements

Add deterministic tests that prove:

1. execution can proceed from a frozen spec artifact
2. frozen-spec execution preserves the current implementation workflow once the task is frozen
3. planning/spec mode and implementation/execution mode remain distinguishable in logs/audit
4. frozen execution logic lives primarily in helper/module code rather than inside `agents/run_task.py`
5. current CLI behavior is preserved unless any new execution-mode surface is explicitly additive

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- execution can proceed deterministically from a frozen spec artifact
- `agents/run_task.py` is thinner after delegating frozen execution logic
