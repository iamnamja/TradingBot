# Task 039c — Machine-Readable Task Contracts (Tests Only)

## Goal

Add deterministic tests for the current machine-readable task contract support in `agents/run_task.py` without changing production code.

## Why

The harness now includes direct support for contract directives in task markdown, including parsing and enforcement inside `validate_static_bundle_contracts(...)`. The next step is to validate that behavior with deterministic tests rather than continuing to evolve the harness through self-modification.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_run_task_contract_directives.py`

The listed file must be materially updated.

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

This task adds tests only.

It must not change:
- `agents/run_task.py`
- provider/model selection behavior
- protected-file policy enforcement
- git / branch behavior
- any file under `src/`

All existing passing tests must continue to pass.

## Current baseline under test — use exact current behavior

Only import symbols that actually exist on the current baseline.

The tests must target these current harness surfaces:

- `parse_task_contract_directives(task_text)`
- `validate_static_bundle_contracts(bundle, task_text)`

It is acceptable to monkeypatch helper functions inside `agents.run_task` to make semantic cases deterministic, including:
- `_module_source_for_name`
- `_class_methods_from_source`
- `_class_init_arity_from_source`

Do NOT patch away `parse_task_contract_directives(...)` or `validate_static_bundle_contracts(...)`.

## Required directive scenarios

Add deterministic tests covering at least:

1. constructor directive parsing
2. forbid-import enforcement
3. forbid-call enforcement
4. config-wrapper enforcement
5. allowed-methods enforcement
6. result-key enforcement
7. backward compatibility when no directives are present

## Strong guidance — use real directive syntax

The task-text fixtures in the tests should use the current markdown directive format, for example:

```text
## Machine-readable contract directives

- CONSTRUCTOR: builder.orchestrator.runner.OrchestratorRunner(config, backlog_tracker, initial_state)
- CONFIG_WRAPPER: builder.orchestrator.runner.OrchestratorRunner first_arg_requires=.config unless=ProjectConfig
- ALLOWED_METHODS: builder.orchestrator.runner.OrchestratorRunner run_next_task run_loop
- FORBID_IMPORTS: builder.orchestrator.backlog BacklogTask BacklogItem BacklogStore TaskRecord
- FORBID_CALLS: runner.run runner.run_all_tasks
- RESULT_KEYS: run_loop processed_tasks stopped_reason final_status approval_required planned_actions
```

## Strong guidance — use deterministic synthetic bundle content

Use synthetic bundle entries such as:

- `tests/test_generated_contracts.py`
- `src/builder/orchestrator/runner.py`

when you need deterministic enforcement checks.

### FORBID_IMPORTS example

Use a synthetic file that contains:

```python
from builder.orchestrator.backlog import BacklogTask
```

Then assert:
- `ok is False`
- `message` contains `"violates FORBID_IMPORTS"`

### FORBID_CALLS / ALLOWED_METHODS example

Use a synthetic file that contains:

```python
runner.run_all_tasks()
```

or:

```python
runner.run()
```

Then assert:
- `ok is False`
- `message` contains `"violates FORBID_CALLS"` or `"violates ALLOWED_METHODS"`

### CONSTRUCTOR / CONFIG_WRAPPER example

Use a synthetic bundle entry that constructs:

```python
OrchestratorRunner(SimpleNamespace(), object(), object())
```

with task directives for `CONSTRUCTOR` and `CONFIG_WRAPPER`, and assert the resulting failure message contains either:
- `"CONSTRUCTOR requires 3"`
- or `"must satisfy CONFIG_WRAPPER"`

### RESULT_KEYS example

Use a synthetic `src/builder/orchestrator/runner.py` bundle entry that contains a `run_loop` implementation but only one of the required keys, for example only `"processed_tasks"`. Then assert:
- `ok is False`
- `message` contains `"missing RESULT_KEYS contract token"`

## Strong guidance — use exact current return/exception behavior

For `parse_task_contract_directives(...)`:
- assert the returned dict structure directly

For `validate_static_bundle_contracts(...)`:
- success is `(True, "")`
- failures are `(False, <message>)`

Do NOT assert invented wrapper dicts like `{"ok": ...}`.

## Import pattern for the test file

Do NOT use:

```python
from agents import run_task
```

Instead, load `agents/run_task.py` by path using `importlib.util.spec_from_file_location(...)`, the same way 039a did.

## Exact forbidden patterns

- modifying `agents/run_task.py`
- creating `last_output.txt`
- creating `_last_agent_model_output.txt`
- creating `_last_agent_file_bundle.txt`
- using wrapper dict expectations for harness functions
- patching away `parse_task_contract_directives(...)`
- patching away `validate_static_bundle_contracts(...)`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- machine-readable task contracts are covered by deterministic tests without production edits
