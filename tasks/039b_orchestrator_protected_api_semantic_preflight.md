# Task 039b — Protected API Semantic Preflight (Tests Only)

## Goal

Add deterministic tests for the current protected Python semantic preflight in `agents/run_task.py` without changing production code.

## Why

The harness now includes protected Python semantic/API drift detection directly in `agents/run_task.py`. The next step is to validate that behavior with stable tests instead of continuing to evolve the harness through task-driven self-modification.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_run_task_protected_api_semantic_preflight.py`

The listed file must be materially updated.

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID
- FILE: tests/test_orchestrator_end_to_end.py MODE=PROTECTED_FORBID

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

The tests must target the current public-ish harness entrypoint:

- `validate_static_bundle_contracts(bundle, task_text)`

Use it as the main assertion surface for semantic preflight behavior.

It is acceptable to monkeypatch helper functions inside `agents.run_task` to make the tests deterministic, including:
- `_module_source_for_name`
- `_class_methods_from_source`
- `_class_init_arity_from_source`

Do NOT patch away `validate_static_bundle_contracts(...)` itself.

## Required semantic scenarios

Add deterministic tests covering at least:

1. valid protected constructor usage passes
2. zero-arg `OrchestratorRunner()` is rejected
3. missing protected method call is rejected
4. missing protected import symbol is rejected
5. bare `SimpleNamespace(...)` first arg is rejected when `.config` is required
6. non-protected modules are ignored by the validator

## Strong guidance — exact fixture shapes

### Import pattern for the test file

Do NOT use:

```python
from agents import run_task
```

Instead, load `agents/run_task.py` by path using `importlib.util.spec_from_file_location(...)`, the same way 039a did, so the test remains portable in the current pytest environment.

### Synthetic module-source fixture

Use a fixture that monkeypatches helper functions with these exact compatible shapes:

```python
def fake_module_source_for_name(module_name, bundle=None):
    ...

def fake_class_methods_from_source(source, class_name):
    ...

def fake_class_init_arity_from_source(source, class_name):
    ...
```

For `fake_class_init_arity_from_source(...)`, return a tuple for `OrchestratorRunner`, for example:

```python
return (3, 3)
```

not a bare integer.

### Example synthetic runner source

Use a synthetic runner source shaped like:

```python
class OrchestratorRunner:
    def __init__(self, config, backlog_tracker, initial_state):
        self.config = config.config if hasattr(config, "config") else config

    def run_next_task(self):
        return None

    def run_loop(self):
        return None
```

### Example project-config source

Use a simple source like:

```python
class ProjectConfig:
    pass
```

### Stable bundle fixture

Construct the synthetic bundle with a file path such as:

- `tests/test_generated_semantic_contract.py`

and put the code-under-test in that bundle entry as a string.

Use normal package imports in the synthetic bundle content, for example:

- `from builder.orchestrator.runner import OrchestratorRunner`
- `from builder.orchestrator.project_config import ProjectConfig`

Do NOT use `src.`-prefixed imports.

### Exact code shapes for scenarios

For the valid case, use:

```python
from builder.orchestrator.project_config import ProjectConfig
from builder.orchestrator.runner import OrchestratorRunner

config = ProjectConfig()
runner = OrchestratorRunner(config, object(), object())
runner.run_next_task()
runner.run_loop()
```

For the zero-arg rejection case, use:

```python
from builder.orchestrator.runner import OrchestratorRunner

runner = OrchestratorRunner()
```

For the missing-method rejection case, use a nonexistent method call such as:

```python
from builder.orchestrator.project_config import ProjectConfig
from builder.orchestrator.runner import OrchestratorRunner

config = ProjectConfig()
runner = OrchestratorRunner(config, object(), object())
runner.run_all_tasks()
```

For the missing-import-symbol rejection case, use:

```python
from builder.orchestrator.runner import MissingSymbol
```

For the bare `SimpleNamespace(...)` rejection case, use:

```python
from types import SimpleNamespace
from builder.orchestrator.runner import OrchestratorRunner

runner = OrchestratorRunner(SimpleNamespace(), object(), object())
```

For the non-protected module case, use something like:

```python
from types import SimpleNamespace

value = SimpleNamespace(answer=42)
```

## Assertion guidance

For success:
- assert `ok is True`
- assert `message == ""`

For failures:
- assert `ok is False`
- assert that `message` contains a stable substring, for example:
  - `"OrchestratorRunner() is called with 0 args"`
  - `"has no method 'run_all_tasks'"`
  - `"imports missing symbol"`
  - `"first arg must be ProjectConfig or object with .config"`

Do NOT require one exact full multi-line message string.

## Exact forbidden patterns

- modifying `agents/run_task.py`
- creating `last_output.txt`
- creating `_last_agent_model_output.txt`
- creating `_last_agent_file_bundle.txt`
- using `src.`-prefixed imports in the synthetic bundle content
- patching `validate_static_bundle_contracts(...)` itself
- returning a bare integer from `fake_class_init_arity_from_source(...)`
- depending on the current real `src/builder/orchestrator/runner.py` file content
- using `runner.run_next_task()` in the missing-method rejection case
- using `from agents import run_task`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- protected API semantic drift is covered by deterministic tests without production edits
