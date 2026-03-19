# Task 038c — Run Loop Decision Logging

## Goal

Add structured decision logging for `run-loop` task iterations without changing any engine semantics.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_run_loop_cli.py`

Both files must be materially updated in the same bundle.

## Harness policy

- FILE: src/builder/orchestrator/runner.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

All existing public APIs and printed output from Task 038b must remain backward compatible.

Do not change the text of the iteration line or final summary.

## Required behavior

If `audit_path` is configured, append one JSON line per real task iteration.

Each decision log entry must include at least:

```python
{
    "task_name": str,
    "outcome": str,
    "timestamp": str,  # ISO format
    "iteration": int,
}
```

## No-task logging rule

Do NOT write a decision log entry for the final no-task sentinel iteration.

If `audit_path` is not configured, skip logging silently.

Do not raise on log write failure in tests; tests should use writable temp paths.

## Exact forbidden patterns

- touching `runner.py`
- changing iteration line format
- changing final summary format
- logging the sentinel no-task iteration
- writing non-JSON log lines
- live GitHub CLI or git integration in tests

## Test requirements

Update `tests/test_orchestrator_run_loop_cli.py` to cover:

- decision log entries are appended for real iterations only
- sentinel no-task iteration is not logged
- log entries contain `task_name`, `outcome`, `timestamp`, `iteration`
- `audit_path` unset skips logging silently

Tests must be deterministic and portable on Windows.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- decision logging happens only for real iterations
- no `runner.py` changes are required
