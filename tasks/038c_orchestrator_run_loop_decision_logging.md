# Task 038c — Run Loop Decision Logging

## Goal

Add structured decision logging for `run-loop` task iterations in the CLI layer only, without changing engine semantics or protected-file behavior.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_run_loop_cli.py`

Both files must be materially updated in the same bundle.

## Harness policy

- FILE: src/builder/orchestrator/runner.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

All existing public APIs and printed output from Task 038b must remain backward compatible.

Do not change:
- the iteration line text format
- the final summary text format
- existing `run-loop` exit code behavior except where explicitly required below

## Required implementation shape

Implement decision logging in the CLI layer.

`cli.main()` must:
1. call `runner.run_loop(...)` in the `run-loop` path
2. print the same iteration and summary text as today
3. append structured JSONL decision-log entries only for real task iterations
4. never log the final no-task sentinel iteration

Do not move logging into `runner.py`.

## Logging behavior

If `audit_path` is configured, append one JSON line per real task iteration.

Each entry must include at least:

```python
{
    "task_name": str,
    "outcome": str,
    "timestamp": str,  # ISO 8601 / UTC-safe string
    "iteration": int,
}
```

### Real iteration definition

A real iteration is one where:
- `task_name != "none"`
- `status != "no_task"`

### Sentinel rule

Do NOT write a decision-log entry for the final no-task sentinel iteration.

### No-audit rule

If `audit_path` is unset or falsey, skip logging silently.

### Failure tolerance

Do not raise if log writing fails. Best effort only.

Create parent directories for `audit_path` when needed.

## Test-shaping requirements

Tests must be written against the current `main` compatibility surface.

### Configuration rule

Do not instantiate `ProjectConfig(...)` with unsupported keyword arguments.

If a test needs `audit_path`, set it after object construction using attribute assignment, for example:

```python
config = ProjectConfig(...)
config.audit_path = str(audit_path)
```

### Runner stubbing rule

Tests may stub `OrchestratorRunner`, but must preserve the current constructor contract from `main`.

Do not assume alternate constructor names like `project_config=` or `backlog=` unless they already exist on `main`.

### Logging assertions

Tests must assert:
- decision-log entries are appended for real iterations only
- sentinel no-task iteration is not logged
- each log entry contains `task_name`, `outcome`, `timestamp`, `iteration`
- `audit_path` unset skips logging silently
- log file parent directories are created when needed

### Output compatibility assertions

Tests must preserve current printed output expectations from Task 038b.
Do not rewrite iteration line or summary expectations unless explicitly required by existing `main`.

## Exact forbidden patterns

- touching `runner.py`
- changing iteration line format
- changing final summary format
- logging the sentinel no-task iteration
- writing non-JSON log lines
- live GitHub CLI or git integration in tests
- changing `ProjectConfig` constructor shape
- adding `audit_path` as a required constructor parameter anywhere

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- decision logging happens only for real iterations
- sentinel no-task iteration is never logged
- logging is best-effort and silent when `audit_path` is unset
- no `runner.py` changes are required
