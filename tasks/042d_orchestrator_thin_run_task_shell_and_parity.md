# Task 042d — Thin `run_task.py` Shell and Parity

## Goal

Validate that `agents/run_task.py` now behaves as a thin orchestration shell over the extracted modules, while preserving current behavior exactly.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_run_task_shell_parity.py`

The listed file must be materially updated.

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

This task must not introduce new product behavior.

This is a **tests-only parity validation task**. By the time 042d runs, the extraction work should already be complete from 042a / 042b / 042c.

The thin shell must preserve the current public workflow:

- task loading
- message construction
- provider execution delegation
- parser/policy delegation
- semantic preflight delegation
- local check execution
- commit/push flow
- runtime artifact cleanup flow

## Test design requirements

The tests must validate the **current shell surface that actually exists in `agents/run_task.py`**.

Do **not** assume or invent any legacy interface that is not present in the current file.

### Specifically:

- Do **not** require `main(argv)` if the current shell only exposes `main()` with argparse reading from `sys.argv`.
- Do **not** assume `--task` or `--non-interactive` flags unless they actually exist in the current parser.
- If invoking `main()`, use the current CLI contract:
  - positional `task`
  - existing optional flags only
  - monkeypatch `sys.argv` instead of requiring a different function signature

### Do not invent nonexistent shell helper names

Do **not** write tests that require helper functions unless those helpers actually exist in the current `agents/run_task.py`.

Examples of names that must **not** be assumed unless present:

- `run_provider`
- `ensure_clean_git`
- `create_branch`
- `commit_changes`
- `push_branch`
- `update_task_state`
- `validate_protected_file_policy`
- `run_semantic_preflight`

### How to validate thin-shell behavior correctly

Prefer validating the shell through the **actual extracted-module delegation points** that now exist, such as:

- provider delegation through `agents.lib.provider_client`
- bundle parsing through `agents.lib.bundle_parser`
- protected-file policy parsing through `agents.lib.protected_file_policy`
- semantic/static contract validation through `agents.lib.semantic_preflight`
- runtime foundations / git / check execution through the current exported wrappers

Runtime artifact handling should be validated through the current cleanup / shell flow, not by inventing parser return shapes that include custom `warnings` fields if the current parser API does not expose them.

## Test requirements

Add deterministic tests that prove:

1. provider call path still delegates through the extracted provider module
2. parser/policy modules are actually used through the current shell/wrapper surface
3. semantic preflight/static validation module is actually used through the current shell/wrapper surface
4. green and failing shell paths still return the expected status
5. push / commit flow still includes runtime artifact cleanup behavior

## Exact forbidden patterns

- new feature work
- behavior changes to retry counts, branch naming, or approval behavior
- moving product logic into tests instead of the extracted modules
- touching orchestrator engine files under `src/builder/orchestrator/`
- touching `agents/run_task.py`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `run_task.py` is validated as a thin shell relative to the prior monolith
- no public behavior changes are introduced
