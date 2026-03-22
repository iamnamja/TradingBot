# Task 046 — Project Bootstrap Adapter

## Goal

Add a bootstrap command that scaffolds a new project adapter/config/task-template set for a new repository.

Continue shrinking `agents/run_task.py` by keeping bootstrap logic in builder/orchestrator/helper modules and limiting the shell to additive routing only.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/project_adapter.py`
- `src/builder/orchestrator/project_config.py`
- `agents/run_task.py`
- `tests/test_project_bootstrap_adapter.py`
- `README.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=main
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_bootstrap_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Critical compatibility requirement

If bootstrap is exposed through `agents/run_task.py`, it must be added **additively** and must not break the current positional `task` workflow.

Do not replace the current execution entrypoint or existing flags.

The goal is:
- bootstrap logic lives in project adapter/config/helper code
- `agents.run_task.main()` only routes additively when bootstrap mode is requested

## Current shell / CLI guidance

If tests invoke `agents.run_task.main()`, they must target the **current** shell surface.

Specifically:

- Do **not** assume `main(argv)` unless it actually exists
- Do **not** assume legacy flags like `--task` or `--non-interactive` unless they actually exist
- If invoking `main()`, monkeypatch `sys.argv` and use the current positional `task` plus existing optional flags only

## Bundle transport safety requirement

Bootstrap scaffolding may include starter docs or task templates that refer to bundle markers.

If generated tests or fixture content need literal strings such as:

- `BEGIN_FILE_BUNDLE`
- `FILE:`
- `END_FILE`
- `END_FILE_BUNDLE`

do **not** place those raw marker strings at the start of a source line inside generated file content.

Use split tokens or concatenation instead.

## Required behavior

Bootstrap should create a minimal reusable starting point for a new client project, including:

- project config skeleton
- adapter factory skeleton
- task folder skeleton
- default validator config
- starter docs/task template references

This should reduce manual setup when using the orchestrator outside TradingBot.

## Test requirements

Add deterministic tests that validate:

1. bootstrap creates the expected scaffold deterministically
2. generated config and adapter stubs are reusable starting points rather than TradingBot-specific copies
3. starter docs/task template references are present
4. any `agents.run_task.py` bootstrap surface is additive and does not break current execution behavior
5. bootstrap logic lives primarily outside `agents/run_task.py`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- a new project adapter/config scaffold can be generated deterministically
- `agents/run_task.py` is thinner after delegating bootstrap logic
