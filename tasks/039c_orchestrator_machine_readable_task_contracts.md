# Task 039c — Machine-Readable Task Contracts (Tests Only)

## Goal

Add deterministic tests for the current machine-readable task-contract support already present in `agents/run_task.py` without changing production code.

## Why

The harness already parses machine-readable task directives and enforces some of them in `validate_static_bundle_contracts(...)`. The next step is to validate that behavior with stable tests instead of continuing to evolve the harness through task-driven self-modification.

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
- bundle parsing behavior
- git / branch behavior
- any file under `src/`

All existing passing tests must continue to pass.

## Current baseline under test — use exact current behavior

Only import symbols that actually exist on the current baseline.

The tests must target these current harness functions:

- `parse_task_contract_directives(task_text)`
- `validate_static_bundle_contracts(bundle, task_text)`

Use `validate_static_bundle_contracts(...)` as the main enforcement surface.

It is acceptable to monkeypatch helper functions inside `agents.run_task` to make tests deterministic, including:
- `_module_source_for_name`
- `_class_methods_from_source`
- `_class_init_arity_from_source`

Do NOT patch away:
- `parse_task_contract_directives(...)`
- `validate_static_bundle_contracts(...)`

## Required directive scenarios

Add deterministic tests covering at least:

1. constructor directive parsing
2. forbid-import enforcement
3. forbid-call enforcement
4. config-wrapper enforcement
5. result-key enforcement
6. backward compatibility when no directives are present

## Strong guidance — exact fixture shapes

### Import pattern for the test file

Do NOT use:

```python
from agents import run_task
```

Instead, load `agents/run_task.py` by path using `importlib.util.spec_from_file_location(...)`.

### Example directive task text

Use a markdown string with a real directive section, for example:

```text
## Machine-readable contract directives

- CONSTRUCTOR: builder.orchestrator.runner.OrchestratorRunner(config, backlog_tracker, initial_state)
- CONFIG_WRAPPER: builder.orchestrator.runner.OrchestratorRunner first_arg_requires=.config unless=ProjectConfig
- ALLOWED_METHODS: builder.orchestrator.runner.OrchestratorRunner run_next_task run_loop
- FORBID_IMPORTS: builder.orchestrator.backlog BacklogTask BacklogItem BacklogStore TaskRecord
- FORBID_CALLS: runner.run runner.run_all_tasks
- RESULT_KEYS: run_loop processed_tasks stopped_reason final_status approval_required planned_actions
```

### Example bundle path

Use a synthetic bundle entry path such as:

- `tests/test_generated_contract_directives.py`

### Example constructor/config-wrapper fixture

Use synthetic bundle code like:

```python
from types import SimpleNamespace
from builder.orchestrator.runner import OrchestratorRunner

runner = OrchestratorRunner(SimpleNamespace(), object(), object())
```

This should fail the config-wrapper contract.

### Example forbid-import fixture

Use synthetic bundle code like:

```python
from builder.orchestrator.backlog import BacklogTask
```

### Example forbid-call fixture

Use synthetic bundle code like:

```python
runner.run_all_tasks()
```

### Example result-keys fixture

Use a synthetic bundle file that mentions the result function token but omits some required result-key tokens so the contract fails, for example content containing:

```python
def some_test():
    run_loop_result = run_loop()
    assert "processed_tasks" in run_loop_result
```

and a directive:

```text
- RESULT_KEYS: run_loop processed_tasks stopped_reason final_status approval_required planned_actions
```

The failure assertion should look for a stable substring like:
- `"missing RESULT_KEYS contract token"`

### Example no-directives fixture

Use task text with no machine-readable directives and assert:
- `parse_task_contract_directives(task_text) == {}`
- `validate_static_bundle_contracts(bundle, task_text)` does not fail solely because directives are absent

## Assertion guidance

For parse tests:
- assert exact directive dictionary content where practical
- for example, `CONSTRUCTOR`, `FORBID_IMPORTS`, and `FORBID_CALLS` lists

For enforcement tests:
- assert `ok is False` for violations
- assert `message` contains a stable substring, for example:
  - `"violates FORBID_IMPORTS"`
  - `"violates FORBID_CALLS"`
  - `"must satisfy CONFIG_WRAPPER"`
  - `"missing RESULT_KEYS contract token"`

Do NOT require one exact full multi-line message string.

## Exact forbidden patterns

- modifying `agents/run_task.py`
- creating `last_output.txt`
- creating `_last_agent_model_output.txt`
- creating `_last_agent_file_bundle.txt`
- using `from agents import run_task`
- patching `validate_static_bundle_contracts(...)` itself
- depending on current real `src/builder/orchestrator/...` production files
- using `src.`-prefixed imports in the synthetic bundle content

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- machine-readable task contract parsing and enforcement are covered by deterministic tests without production edits
