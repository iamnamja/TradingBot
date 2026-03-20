# Task 039b — Machine-Readable Task Contracts

## Goal

Teach `agents/run_task.py` to read machine-readable contract directives from task specs and enforce them before bundle write / test execution.

## Why

The current harness depends too much on prose in task specs. That works when tasks are extremely specific, but it still allows semantic drift because the contract is not structured enough for the harness to enforce directly.

This task adds explicit task directives that the harness can parse and validate deterministically.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `tests/test_run_task_contract_directives.py`

Both listed files must be materially updated.

## Scope

Keep the change narrowly focused on task-spec directive parsing and enforcement.

Do not change:
- provider/model selection behavior
- protected-file policy enforcement
- git / branch behavior
- TradingBot or orchestrator production code under `src/`

## Required directive support

Add support for task-spec directives like these:

```text
- CONSTRUCTOR: builder.orchestrator.runner.OrchestratorRunner(config, backlog_tracker, initial_state)
- CONFIG_WRAPPER: builder.orchestrator.runner.OrchestratorRunner first_arg_requires=.config unless=ProjectConfig
- ALLOWED_METHODS: builder.orchestrator.runner.OrchestratorRunner run_next_task run_loop
- FORBID_IMPORTS: builder.orchestrator.backlog BacklogTask BacklogItem BacklogStore TaskRecord
- FORBID_CALLS: runner.run runner.run_all_tasks
- RESULT_KEYS: run_loop processed_tasks stopped_reason final_status approval_required planned_actions
```

The syntax can be normalized if needed, but it must remain human-writable in markdown task files.

## Required behavior

The harness must:

1. parse directives from the task text
2. validate generated bundles against those directives before write / test execution
3. produce actionable error messages that reference the violated directive

Examples:

- calling `runner.run_all_tasks()` when `FORBID_CALLS` blocks it
- importing `BacklogTask` when `FORBID_IMPORTS` blocks it
- constructing `OrchestratorRunner` with the wrong contract when `CONSTRUCTOR` + `CONFIG_WRAPPER` say otherwise
- asserting on missing result keys when `RESULT_KEYS` says what the current return contract must include

## Directive design constraints

- directives must be additive and backward compatible with older task specs
- if a task does not use directives, current behavior should continue unchanged
- parsing must be deterministic and Windows-portable
- directives must be usable in plain markdown task files without custom tooling

## Tests

`tests/test_run_task_contract_directives.py` must include deterministic tests for at least:

1. constructor directive parsing
2. forbid-import enforcement
3. forbid-call enforcement
4. config-wrapper enforcement
5. result-key enforcement
6. backward compatibility when no directives are present

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- the harness can enforce structured task contracts without depending only on prose
