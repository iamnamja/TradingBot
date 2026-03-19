# Task 038b — Run Loop CLI Surface

## Goal

Wire the CLI to expose a `run-loop` mode that calls `runner.run_loop(max_tasks=...)` and prints the required iteration lines and final summary.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_run_loop_cli.py`

Both files must be materially updated in the same bundle.

## Harness policy

- FILE: src/builder/orchestrator/runner.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

All existing public APIs must remain backward compatible:

- existing `run-once` behavior must continue to work
- existing `simulate` behavior must continue to work
- existing resume behavior must not be removed or renamed
- `runner.py` must not be modified in this task

All existing passing tests must continue to pass.

## Required behavior

The CLI must support a `run-loop` mode that:

1. constructs the runner exactly as current CLI code already does
2. calls `runner.run_loop(max_tasks=...)`
3. prints one line per processed task in this exact format:

```text
[Task N] task_name — outcome (next_action)
```

4. prints a final summary in this exact format:

```text
Run complete: {final_status}
Tasks processed: {count}
Stopped reason: {reason}
```

## Input rules

- `--max-tasks` must be optional and default to `100`
- `run-loop` must not require any new mandatory arguments
- do not add any new runner constructor arguments

## Exact forbidden patterns

- touching `runner.py`
- changing `run_next_task()`
- changing guardrail semantics
- writing decision logs in this task
- relying on live git state in tests
- relying on actual repo `tasks/` contents
- Unix-only shell commands

## Test requirements

`tests/test_orchestrator_run_loop_cli.py` must cover:

- CLI run-loop calls `runner.run_loop(max_tasks=...)`
- iteration line formatting is exact
- final summary formatting is exact
- `--max-tasks` is respected and forwarded
- existing CLI modes still parse and dispatch

Tests must mock the runner and remain deterministic on Windows.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- CLI run-loop works without any `runner.py` changes
- printed output matches the exact required strings
