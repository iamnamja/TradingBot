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
- Do **not** assume `agents` is importable as a package in tests unless the current repo actually exposes it that way
- When loading `agents/run_task.py` with `runpy.run_path(...)`, do **not** assume mutating the returned dict automatically patches `main.__globals__`; patch the actual callable seam used by the shell
- For CLI-surface preservation tests, patch `main.__globals__[...]` or an existing exported seam such as `_runtime_foundations_exports()` rather than inventing a new interception path

## 044a artifact-schema compatibility requirement

This task builds on 044a and must preserve the existing frozen-spec artifact contract.

Do **not** rename or remove stable artifact fields already validated by 044a tests.

At minimum, the frozen-spec artifact produced by `agents/lib/spec_mode.py` must continue to preserve the 044a-compatible fields and behavior that existing tests rely on, including:

- top-level `mode`
- top-level `task_path`
- top-level `source_hash`
- top-level `frozen_spec`
- top-level `verification_commands`
- deterministic artifact content for the same task input

It is acceptable to add new additive fields for execution mode, such as:

- `artifact_kind`
- `artifact_path`
- `canonical_task_text`
- `frozen_spec_path`

But those additions must **not** break or rewrite the established 044a artifact shape.

## Bundle transport safety requirement

This task is transmitted through the runner's file-bundle protocol.

If generated tests need to refer to literal bundle markers or frozen-task snippets that contain them, do **not** place raw marker strings such as `FILE:` or `END_FILE` at the start of a source line inside generated test content.

Use split tokens or concatenation instead.

## Required behavior

Execution mode should:

- accept a frozen spec artifact as the canonical task input
- resolve the canonical task text from the frozen artifact before the normal implementation loop continues
- preserve current execution behavior once the task is frozen
- keep the distinction between planning/spec work and implementation/execution mode visible in logs/audit

If new helper functions are added in `agents/lib/spec_mode.py`, expose them through `_spec_mode_exports()` **additively** rather than replacing existing exports.

## Test requirements

Add deterministic tests that prove:

1. execution can proceed from a frozen spec artifact
2. frozen-spec execution preserves the current implementation workflow once the task is frozen
3. planning/spec mode and implementation/execution mode remain distinguishable in logs/audit
4. frozen execution logic lives primarily in helper/module code rather than inside `agents/run_task.py`
5. current CLI behavior is preserved unless any new execution-mode surface is explicitly additive
6. 044a frozen-spec artifact tests continue to pass unchanged

Tests should:

- prefer the same import/loading pattern already used successfully in the existing shell-parity/runtime-foundations tests
- avoid direct `from agents.lib import ...` imports unless that import path is already valid in the repo test environment
- avoid brittle monkeypatching against a detached `runpy.run_path()` return dict when the live callable uses a different globals dict

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- execution can proceed deterministically from a frozen spec artifact
- existing 044a spec-mode tests remain green
- `agents/run_task.py` is thinner after delegating frozen execution logic
