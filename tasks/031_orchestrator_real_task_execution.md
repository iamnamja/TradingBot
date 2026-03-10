# Task 031 — Orchestrator Real Task Execution

## Goal

Add an optional real execution bridge to the orchestrator so it can invoke the project task runner for a selected task file, while preserving all existing orchestrator behavior, public APIs, and test expectations by default.

## Why

Up to task 030, the orchestrator can discover the backlog, simulate execution across real task files, and evaluate review / approval logic. However, `execute_task()` still returns a mocked success payload. The next milestone is to let the orchestrator execute one backlog task for real.

## Critical compatibility requirement

This task must be implemented as a backward-compatible extension.

The new real execution path must be opt-in.

If no real task-runner command is explicitly configured, the orchestrator must preserve the current legacy/mock execution behavior so all existing tests continue to pass.

Do not break or change the observable behavior of existing orchestrator features unless the new real-execution path is explicitly being used.

The following public APIs must remain backward compatible:

- `ProjectAdapter(config=...)`
- `ProjectAdapter.get_tradingbot_default_config()`
- `ProjectAdapter.get_generic_project_config()`
- `OrchestratorRunner(config, backlog_tracker, initial_state)`
- `OrchestratorRunner.select_next_task()`
- `OrchestratorRunner.run_next_task(dry_run=False)`
- `OrchestratorRunner.simulate_backlog()`

## Scope

Implement an optional real execution bridge inside the orchestrator that:

- resolves the selected task file path from the configured tasks directory
- invokes the project task runner command for that task when explicitly configured
- captures stdout, stderr, and exit code
- returns a structured execution payload

## Deliverables

Create or update these exact files, and every listed existing file must be materially updated in the same bundle:

- src/builder/orchestrator/runner.py
- src/builder/orchestrator/project_config.py
- src/builder/orchestrator/project_adapter.py
- src/builder/orchestrator/cli.py
- tests/test_orchestrator_real_execution.py
- tests/test_project_adapter.py
- tests/test_multi_project_adapters.py

## Bundle completeness requirement

The bundle is incomplete unless **all seven deliverables** are present.

This task must not be completed with only implementation-file changes.

In particular:

- `tests/test_project_adapter.py` must always appear in the bundle
- `tests/test_multi_project_adapters.py` must always appear in the bundle
- `tests/test_orchestrator_real_execution.py` must always appear in the bundle

If the agent changes `project_adapter.py` or `project_config.py`, it must also materially update both adapter-related test files in the same bundle.

If the agent changes `runner.py`, it must materially update `tests/test_orchestrator_real_execution.py` in the same bundle.

## Required behavior

1. Add task-runner configuration to the project config layer.

2. `ProjectConfig` must remain backward compatible:
   - adding `task_runner_command` is allowed
   - it must be optional or have a safe default value
   - existing constructor calls without that field must still work

3. `ProjectAdapter(config=...)` must still work.

4. `ProjectAdapter.get_tradingbot_default_config()` must still exist.

5. `ProjectAdapter.get_generic_project_config()` must still exist.

6. `OrchestratorRunner.__init__` must keep the existing constructor signature:
   - `config`
   - `backlog_tracker`
   - `initial_state`

7. `OrchestratorRunner.select_next_task()` must still exist.

8. `OrchestratorRunner.simulate_backlog()` must still exist and keep current behavior.

9. `run_next_task(dry_run=True)` must preserve the current dry-run response contract, including existing keys expected by tests.

10. `run_next_task()` when no pending tasks exist must preserve the current no-task response contract, including existing keys expected by tests.

11. `execute_task()` must support two modes:

### Legacy/default mode

If no explicit real task-runner command is configured, preserve the current legacy/mock behavior so existing tests continue to pass.

This means the default path must NOT try to run a subprocess like `default_task_runner`.

### Real execution mode

If an explicit real task-runner command is configured, `execute_task()` may invoke it and return a structured result.

12. Real execution mode must capture:
   - stdout
   - stderr
   - returncode
   - resolved task file path

13. The real execution result must look like:

{
    "success": bool,
    "status": str,
    "stdout": str,
    "stderr": str,
    "returncode": int,
    "task_file": str
}

## Ownership and typing constraints

The following ownership rules are mandatory:

- `ProjectConfig` is a data container only.
- Do NOT move `get_tradingbot_default_config()` onto `ProjectConfig`.
- Do NOT move `get_generic_project_config()` onto `ProjectConfig`.
- Those factory methods must remain on `ProjectAdapter`.

The following constructor/API rules are mandatory:

- `ProjectAdapter(config=...)` must continue to work.
- `OrchestratorRunner(config, backlog_tracker, initial_state)` must continue to work.
- `run_next_task()`, `select_next_task()`, and `simulate_backlog()` must continue to exist.

The following default-config rules are mandatory:

- `ProjectAdapter.get_tradingbot_default_config().task_runner_command is None`
- `ProjectAdapter.get_generic_project_config().task_runner_command is None`

The following execution rules are mandatory:

- If `task_runner_command is None`, preserve the existing mock/default execution path.
- Do not execute a subprocess in the default path.
- Do not use `"default_task_runner"` as a fallback command.

The following typing rules are mandatory:

- Do not introduce runtime NameError issues from type annotations.
- If a type annotation refers to the enclosing class, use a safe forward reference or `from __future__ import annotations`.
- The implementation must pass `ruff` and test collection on import.

## Required implementation guidance

- Do not remove `simulate_backlog()`.
- Do not change the constructor signature of `OrchestratorRunner`.
- Do not remove `ProjectAdapter.get_generic_project_config()`.
- Do not remove `ProjectAdapter(config=...)`.
- Do not make review behavior stricter by default in this task.
- Do not change the existing success-path semantics of `run_next_task()` for tests that do not explicitly exercise the real execution bridge.
- Do not change the existing failure message contract unless a new test explicitly requires it.
- Do not remove existing result keys like `dry_run`, `outcome`, `next_action`, or `requires_approval` where current tests expect them.
- Avoid introducing unused variables or dead code.
- Keep the real execution path explicit and testable.
- Extend existing classes; do not replace them with incompatible interfaces.

## Acceptance criteria

Unit tests verify:

- task path resolution works in real execution mode
- a configured real task-runner command can be invoked
- failed command execution yields `success=False`
- dry-run does not execute the command

`tests/test_project_adapter.py`, `tests/test_multi_project_adapters.py`, and `tests/test_orchestrator_real_execution.py` must all be materially updated in the same bundle.

A material update means at least one new assertion, changed expectation, or new test case relevant to:

- task-runner configuration
- backward compatibility
- exact legacy runner contract
- cross-platform real execution behavior

Re-outputting the same test file or changing whitespace/comments only is insufficient.

Also required:

- all pre-existing orchestrator tests continue to pass
- `simulate_backlog()` remains available and passing
- `tests/test_project_adapter.py` continues to pass
- `tests/test_multi_project_adapters.py` continues to pass
- `tests/test_orchestrator_real_execution.py` continues to pass

## Normative compatibility examples

The following behaviors are required and must remain true after this task.

### Runner behavior compatibility

The following methods must remain implemented on `OrchestratorRunner`:

- `select_next_task()`
- `run_next_task(dry_run=False)`
- `simulate_backlog()`

`run_next_task()` must preserve existing behavior used by prior tests.

### Exact legacy runner contract

In the default legacy/mock path, `OrchestratorRunner` must preserve the existing workflow contract used by prior tests.

`select_next_task()` must:

- call `backlog_tracker.scan_tasks()`
- pass the scanned tasks to `backlog_tracker.get_next_task(...)`
- return that selected task

`run_next_task()` must:

- use `select_next_task()`
- not hardcode `"001_task.py"`
- not invent placeholder task names
- not omit existing result keys

### Legacy execution behavior must match prior tests exactly

When a pending task exists in the legacy/default path:

- `task_name == "001_task.py"` for the selected task in existing tests
- `status == "running"`
- `message == "Task is now running."`
- `outcome == "ready_for_pr"`
- `next_action == "merge"`

Do not return placeholder values such as:

- `"mock_task"`
- `status == "mocked"`

When no pending task exists:

- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`
- `outcome == "noop"`

Do not hardcode a task name when no task exists.

### Dry-run behavior must match prior tests exactly

When `dry_run=True` and a task exists:

- `dry_run is True`
- `task_name == "001_task.py"` for the selected task in existing tests
- `status == "planned"`
- `message == "Task is planned for execution."`
- `outcome == "noop"`

When `dry_run=True` and no task exists:

- `dry_run is True`
- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`
- `outcome == "noop"`

Do not replace the old result contract with a smaller dictionary.

Preserve existing keys such as:

- `task_name`
- `status`
- `message`
- `dry_run`
- `outcome`
- `next_action`
- `requires_approval`

### Exact simulation compatibility

`simulate_backlog()` must remain implemented and must return a dictionary with the existing keys expected by tests:

- `processed_tasks`
- `stopped_reason`
- `final_status`
- `approval_required`
- `planned_actions`

### Project adapter compatibility

`ProjectAdapter.get_tradingbot_default_config()` must return a config where:

- `tasks_directory == "tasks/"`
- `lint_command == "ruff check ."`
- `test_command == "pytest -q"`
- `task_runner_command is None`

`ProjectAdapter.get_generic_project_config()` must return a config where:

- `tasks_directory == "generic_tasks/"`
- `lint_command == "flake8 ."`
- `test_command == "pytest tests/test_generic.py"`
- `task_runner_command is None`

`ProjectAdapter(config=project_config)` must still be valid.

### Runner API compatibility

The following methods must still exist:

- `select_next_task()`
- `run_next_task(dry_run=False)`
- `simulate_backlog()`

### Existing result-contract examples

When there are no pending tasks, `run_next_task()` must still return values compatible with existing tests, including:

- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`
- `outcome == "noop"`

When `dry_run=True`, existing dry-run keys must still be present, including:

- `dry_run`
- `task_name`
- `status`
- `message`
- `outcome`

### Execution mode requirement

The real execution bridge must be opt-in.

If `task_runner_command is None`, preserve the legacy/mock behavior and do not execute a subprocess.

Do not use `"default_task_runner"` as a default.

### Typing / implementation requirement

Do not introduce forward-reference NameError issues in annotations.

If self-referential type annotations are used, make them safe for runtime import and test collection.

### Exact real execution test portability rule

`tests/test_orchestrator_real_execution.py` must be materially updated to avoid plain `echo`.

The real execution test must use a cross-platform-safe command, such as invoking the current Python interpreter with a short `-c` command.

Do not use plain `echo` as the subprocess executable on Windows.

## Guardrails

- Do not remove simulation mode
- Do not hardcode project-specific behavior in core orchestrator classes
- Do not parse task output here beyond minimal structural normalization
- Do not break backward compatibility in `ProjectConfig`
- Do not break backward compatibility in `ProjectAdapter`
- Do not break backward compatibility in `OrchestratorRunner`
- Do not execute a subprocess in the default/legacy path