# Task 040 — Multi-Project Hardening

## Current baseline update

Task 037 established a stable `runner.py` baseline. For this task, treat the current `runner.py` on `main` as protected and locked.

Primary work should be in project configuration and adapter code plus tests.

## Goal

Remove hidden project-specific assumptions from the orchestrator so it works correctly with any project configuration, not just TradingBot.

## Why

The orchestrator currently has implicit assumptions about TradingBot's directory layout, file patterns, and runner command. These must become fully configurable so the same orchestrator code can drive any project.

## Critical compatibility requirement

All existing public APIs must remain backward compatible:
- `ProjectAdapter.get_tradingbot_default_config()` must still exist and work
- `ProjectAdapter.get_generic_project_config()` must still exist and work
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged
- `simulate_backlog()` signature and return contract unchanged

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `tests/test_project_adapter.py`
- `tests/test_multi_project_adapters.py`

All four files must be materially updated in the same bundle.

## CRITICAL — runner.py is PROTECTED and must NOT be included

`src/builder/orchestrator/runner.py` is a stable, fully-tested file. Do NOT include it in the bundle.
Do NOT rewrite it. Do NOT modify it. Do NOT include it as a deliverable.

This task must be completed without touching `runner.py`.

## Bundle completeness requirement

The bundle is incomplete unless all four deliverables are present.

## Required behavior

### project_config.py

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

Do NOT use `@dataclass(frozen=True)`. All fields must be mutable after construction.

### project_adapter.py

`ProjectAdapter.get_tradingbot_default_config()` must return a `ProjectConfig` with:
- `task_runner_command = None`
- `state_path = None`
- all existing TradingBot fields preserved

`ProjectAdapter.get_generic_project_config()` must return a `ProjectConfig` with:
- `task_runner_command = None`
- `state_path = None`
- generic/neutral values for all fields

Both factory methods must remain on `ProjectAdapter`.

## CRITICAL — optional config access compatibility

Because `runner.py` already uses `getattr(...)` for optional fields after Task 037, this task must preserve compatibility with that style.

Do not make config changes that would force `runner.py` changes.

## Locked runner contracts

Do not change any existing runner behavior, including:
- success path
- review-blocked path
- failure path
- no-task path
- dry-run path
- guardrail path
- simulation contract
- execute_task default mock behavior

## Multi-project test requirements

`tests/test_multi_project_adapters.py` must demonstrate the orchestrator working with at least two distinct project configurations:

1. TradingBot config
2. A second generic/hypothetical project config with different:
   - `tasks_directory`
   - `branch_naming_pattern`
   - `task_file_pattern`
   - `lint_command`
   - `test_command`

Tests must verify that `OrchestratorRunner` works correctly with both configs without any production code changes.

## Exact forbidden patterns

- touching `runner.py`
- hardcoded TradingBot-specific paths or patterns in orchestrator core beyond the TradingBot adapter factory
- moving factory methods from `ProjectAdapter` to `ProjectConfig`
- `@dataclass(frozen=True)` on config classes
- breaking mutability after construction
- unused locals or imports that ruff will flag

## Acceptance criteria

- `get_tradingbot_default_config()` returns config with `task_runner_command is None`
- `get_generic_project_config()` returns config with `task_runner_command is None`
- config fields are mutable after construction
- at least two distinct project configs are tested
- no hidden TradingBot assumptions remain in config/adapters
- existing orchestrator tests remain green without modifying runner

`ruff check .` must pass. `pytest -q` must be fully green.

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.
