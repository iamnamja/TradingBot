# Task 041a — Project Config Schema Hardening

## Goal

Make project configuration explicitly support optional multi-project fields without changing any runner or CLI code.

## Why

This task is the only production-code task in the 041 workstream.

Recent 039/040 work showed that schema/config changes should be isolated first, and later tasks should validate the new baseline instead of continuing to modify engine behavior.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `tests/test_project_adapter.py`

All three files must be materially updated in the same bundle.

## Harness policy

- FILE: src/builder/orchestrator/runner.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/cli.py MODE=PROTECTED_FORBID

## Machine-readable contract directives

- FORBID_IMPORTS: builder.orchestrator.runner OrchestratorRunner
- FORBID_IMPORTS: builder.orchestrator.cli main run_cli
- FORBID_CALLS: runner.run runner.run_all_tasks
- RESULT_KEYS: project_config tasks_directory lint_command test_command branch_naming_pattern protected_file_patterns artifact_path_patterns approval_required_file_patterns task_runner_command state_path task_file_pattern audit_path

## Required behavior

`ProjectConfig` must support these configurable fields, with safe defaults where appropriate:

```python
@dataclass
class ProjectConfig:
    tasks_directory: str
    lint_command: str
    test_command: str
    branch_naming_pattern: str
    protected_file_patterns: list[str]
    artifact_path_patterns: list[str]
    approval_required_file_patterns: list[str]
    task_runner_command: str | None = None
    state_path: str | None = None
    task_file_pattern: str = "*.md"
    audit_path: str | None = None
```

Do NOT use `@dataclass(frozen=True)`.

## Adapter requirements

`ProjectAdapter.get_tradingbot_default_config()` must still exist and preserve current TradingBot defaults, including:

- `task_runner_command is None`
- `state_path is None`
- `audit_path is None` unless explicitly configured elsewhere
- current TradingBot task / lint / test defaults remain intact

`ProjectAdapter.get_generic_project_config()` must still exist and return a neutral non-TradingBot config, with:

- `task_runner_command is None`
- `state_path is None`
- generic lint/test commands
- a non-TradingBot `tasks_directory`
- a different `branch_naming_pattern`
- a different `task_file_pattern`

## CRITICAL baseline rules

This task must not touch runner/CLI engine behavior.

Do NOT:
- modify `runner.py`
- modify `cli.py`
- move factory methods from `ProjectAdapter` into `ProjectConfig`
- freeze the dataclass
- break field mutability after construction

## Test requirements

`tests/test_project_adapter.py` must verify all of:

1. config fields are mutable after construction
2. both factory methods still exist
3. optional fields are present and default correctly
4. TradingBot defaults remain intact
5. generic config is distinct from TradingBot on:
   - `tasks_directory`
   - `branch_naming_pattern`
   - `task_file_pattern`

## Exact forbidden patterns

- touching `runner.py`
- touching `cli.py`
- importing or instantiating `OrchestratorRunner`
- `@dataclass(frozen=True)` on config classes
- breaking mutability after construction
- introducing unused imports or locals that `ruff` will flag

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- no engine files are touched
- config schema supports the optional multi-project fields cleanly
