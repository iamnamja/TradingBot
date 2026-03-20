# Task 040b — Multi-Project Adapter Validation

## Goal

Demonstrate the orchestrator working with at least two distinct project configurations without touching engine files.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/project_adapter.py`
- `tests/test_multi_project_adapters.py`

Both files must be materially updated in the same bundle.

## Harness policy

- FILE: src/builder/orchestrator/runner.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/cli.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

All existing public APIs must remain backward compatible:

- `ProjectAdapter.get_tradingbot_default_config()` must still exist and work
- `ProjectAdapter.get_generic_project_config()` must still exist and work
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged
- `simulate_backlog()` signature unchanged
- `run_loop(max_tasks=100)` signature unchanged

## Multi-project test requirements

`tests/test_multi_project_adapters.py` must demonstrate the orchestrator working with at least:

1. TradingBot config
2. A second generic project config with different:
   - `tasks_directory`
   - `branch_naming_pattern`
   - `task_file_pattern`
   - `lint_command`
   - `test_command`

Tests must verify that `OrchestratorRunner` works with both configs without any production code changes outside adapter/config files.

## Exact forbidden patterns

- touching `runner.py`
- touching `cli.py`
- hardcoded TradingBot-specific paths or patterns in orchestrator core beyond the TradingBot adapter factory
- breaking config mutability
- unused locals or imports that ruff will flag

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- at least two distinct project configs are exercised
- no hidden TradingBot assumptions remain in config/adapters
