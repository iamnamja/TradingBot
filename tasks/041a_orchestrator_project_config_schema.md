# Task 040a — Project Config Schema Hardening

## Goal

Make project configuration explicitly support optional multi-project fields without changing any runner or CLI code.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `tests/test_project_adapter.py`

All three files must be materially updated in the same bundle.

## Harness policy

- FILE: src/builder/orchestrator/runner.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/cli.py MODE=PROTECTED_FORBID

## Required behavior

`ProjectConfig` must support these configurable fields (all optional with safe defaults where appropriate):

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

`ProjectAdapter.get_tradingbot_default_config()` must still exist and preserve current TradingBot defaults, with:

- `task_runner_command is None`
- `state_path is None`
- `audit_path is None` unless explicitly configured elsewhere

`ProjectAdapter.get_generic_project_config()` must still exist and return a neutral non-TradingBot config, with:

- `task_runner_command is None`
- `state_path is None`
- generic lint/test commands
- a non-TradingBot `tasks_directory`
- a different `branch_naming_pattern`
- a different `task_file_pattern`

## Exact forbidden patterns

- touching `runner.py`
- touching `cli.py`
- moving factory methods from `ProjectAdapter` into `ProjectConfig`
- `@dataclass(frozen=True)` on config classes
- breaking mutability after construction

## Test requirements

`tests/test_project_adapter.py` must verify:

- config fields are mutable after construction
- both factory methods still exist
- optional fields are present and default correctly
- TradingBot defaults remain intact

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- no engine files are touched
