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

Create or update these exact files:

- src/builder/orchestrator/runner.py
- src/builder/orchestrator/project_config.py
- src/builder/orchestrator/project_adapter.py
- src/builder/orchestrator/cli.py
- tests/test_orchestrator_real_execution.py
- tests/test_project_adapter.py
- tests/test_multi_project_adapters.py

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

Also required:

- all pre-existing orchestrator tests continue to pass
- `simulate_backlog()` remains available and passing
- `tests/test_project_adapter.py` continues to pass
- `tests/test_multi_project_adapters.py` continues to pass

## Guardrails

- Do not remove simulation mode
- Do not hardcode project-specific behavior in core orchestrator classes
- Do not parse task output here beyond minimal structural normalization
- Do not break backward compatibility in `ProjectConfig`
- Do not break backward compatibility in `ProjectAdapter`
- Do not break backward compatibility in `OrchestratorRunner`
- Do not execute a subprocess in the default/legacy path