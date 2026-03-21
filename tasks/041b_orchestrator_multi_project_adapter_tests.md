# Task 041b — Multi-Project Adapter Validation (Tests Only)

## Goal

Demonstrate the orchestrator working with at least two distinct project configurations using the baseline produced by Task 041a, without touching engine files.

## Why

Recent 039/040 work showed that once the production baseline is in place, follow-on tasks should be tests-only whenever possible.

This task is therefore validation-only. It should not modify production code.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_multi_project_adapters.py`

The listed file must be materially updated.

## Harness policy

- FILE: src/builder/orchestrator/runner.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/cli.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/backlog.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/execution_result.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/project_adapter.py MODE=PROTECTED_FORBID
- FILE: src/builder/orchestrator/project_config.py MODE=PROTECTED_FORBID

## Machine-readable contract directives

- CONSTRUCTOR: builder.orchestrator.runner.OrchestratorRunner(config, backlog_tracker, initial_state)
- CONFIG_WRAPPER: builder.orchestrator.runner.OrchestratorRunner first_arg_requires=.config unless=ProjectConfig
- ALLOWED_METHODS: builder.orchestrator.runner.OrchestratorRunner run_next_task run_loop
- FORBID_IMPORTS: builder.orchestrator.backlog BacklogTask BacklogItem BacklogStore TaskRecord TaskState
- FORBID_IMPORTS: builder.orchestrator.execution_result ExecutionResult
- FORBID_CALLS: runner.run runner.run_all_tasks
- RESULT_KEYS: run_loop processed_tasks stopped_reason final_status approval_required planned_actions

## Critical compatibility requirement

All existing public APIs must remain backward compatible:

- `ProjectAdapter.get_tradingbot_default_config()` must still exist and work
- `ProjectAdapter.get_generic_project_config()` must still exist and work
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged
- `run_loop(max_tasks=100)` signature unchanged

## Current baseline under test

This task must validate the real current baseline on `main`.

The test file should exercise:

1. TradingBot config
2. a second generic project config with different:
   - `tasks_directory`
   - `branch_naming_pattern`
   - `task_file_pattern`
   - `lint_command`
   - `test_command`

The tests must verify that `OrchestratorRunner` works with both configs without any production code changes.

## Required test construction rules

Build the runner using the real constructor surface.

For config shape, use either:
- a real `ProjectConfig`, or
- a lightweight wrapper object exposing `.config` where `.config` has the required fields

Do NOT pass a bare `SimpleNamespace(...)` directly as the first constructor argument to `OrchestratorRunner`.

Use `OrchestratorState(tasks=[])` for `initial_state`.

Use lightweight stub backlog tracker objects exposing only the methods the real runner needs:
- `scan_tasks()`
- `load_state(path)`
- `save_state(path, tasks)`
- `get_next_task(tasks)`

Use lightweight stub task objects exposing:
- `name`
- `order`
- `status`

For `run_loop()` scenarios, prefer patching `runner.run_next_task` directly.

For `run_next_task()` scenarios, patch only the minimal backlog/state behavior needed to exercise the real method.

## Required validation scenarios

`tests/test_multi_project_adapters.py` must include deterministic tests for at least:

1. TradingBot config factory returns a usable config
2. generic config factory returns a distinct usable config
3. runner can be constructed with TradingBot config
4. runner can be constructed with generic config
5. `run_next_task(dry_run=True)` works with both configs when backlog/state is minimally stubbed
6. `run_loop()` can process patched task results with both configs
7. no TradingBot-only assumptions leak into generic config behavior

## CRITICAL baseline behavior details

When patching `backlog_tracker.load_state(path)` for `run_next_task()` tests, return a plain list such as `[]`, not an `OrchestratorState(...)`, because `read_backlog()` iterates the returned state list directly.

When asserting `run_loop()` results, use the current human-readable baseline values, for example:
- `"No pending tasks available."`
- `"Execution failed."`
- `"Approval required"`

Do NOT assert symbolic stop codes like:
- `"no_task"`
- `"failed"`
- `"approval_required"`

## Exact forbidden patterns

- touching `runner.py`
- touching `cli.py`
- touching `backlog.py`
- touching `execution_result.py`
- touching `project_adapter.py`
- touching `project_config.py`
- hardcoded TradingBot-only assumptions in test expectations for the generic config
- real subprocess calls
- relying on live git state or GitHub CLI
- relying on actual repo `tasks/` contents
- zero-argument `OrchestratorRunner()`
- bare `SimpleNamespace(...)` passed directly as the root config argument
- calling nonexistent methods like `runner.run()` or `runner.run_all_tasks()`
- importing nonexistent symbols such as:
  - `BacklogTask`
  - `BacklogItem`
  - `BacklogStore`
  - `TaskRecord`
  - `TaskState`
  - `ExecutionResult`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- at least two distinct project configs are exercised
- no engine files are touched
- no hidden TradingBot assumptions remain in config/adapters
