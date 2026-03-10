# Task 031 — Orchestrator Real Task Execution

## Goal

Add a real execution bridge to the orchestrator so it can invoke the project task runner for a selected task file, while preserving all existing orchestrator behavior and tests.

## Why

Up to task 030, the orchestrator can discover the backlog, simulate execution across real task files, and evaluate review / approval logic. However, `execute_task()` still returns a mocked success payload. The next milestone is to let the orchestrator execute one backlog task for real.

## Critical compatibility requirement

This task must be implemented as a backward-compatible extension.

Do not break or change the observable behavior of existing orchestrator features unless the new real-execution path is explicitly being used.

In particular:

- `simulate_backlog()` must remain present and keep its existing behavior.
- Existing tests from tasks 021–030 must continue to pass without being rewritten for new defaults.
- Existing success-path runner tests must still return the same default status / message / outcome they returned before this task.
- Existing failure-path tests must preserve current failure wording, including:

  Execution failed: Execution failed

- `ProjectConfig` must remain backward compatible with existing constructor calls in the test suite.

## Scope

Implement a real execution bridge inside the orchestrator that:

- resolves the selected task file path from the configured tasks directory
- invokes the project task runner command for that task
- captures stdout, stderr, and exit code
- returns a normalized execution payload for downstream review / policy / repair logic

## Deliverables

Create or update these exact files:

- src/builder/orchestrator/runner.py
- src/builder/orchestrator/project_config.py
- src/builder/orchestrator/project_adapter.py
- src/builder/orchestrator/cli.py
- tests/test_orchestrator_real_execution.py

## Required behavior

1. Add task-runner configuration to the project config layer.

2. `ProjectConfig` must remain backward compatible:

   - adding `task_runner_command` is allowed
   - but it must be optional or have a safe default
   - existing tests that construct `ProjectConfig(...)` without that field must still work

3. The project adapter must define a task-runner command template for the TradingBot default config.

4. `OrchestratorRunner.execute_task()` must support a real command-execution path.

5. Dry-run mode must not execute the task runner.

6. The existing simulation path from task 030 must remain intact.

7. The existing default runner behavior used by older tests must remain intact unless the new real-execution configuration is explicitly exercised.

8. Real execution must capture:

   - stdout
   - stderr
   - returncode
   - resolved task file path

Execution must return a structured dictionary like:

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
- Do not make review behavior stricter by default in this task.
- Do not change the existing success-path semantics of `run_next_task()` for tests that do not explicitly exercise the real execution bridge.
- Do not change the existing failure message contract unless a new test explicitly requires it.
- Avoid introducing unused variables or dead code.
- Keep the real execution path explicit and testable.

## Acceptance criteria

Unit tests verify:

- task path resolution works
- a configured real task-runner command can be invoked
- failed command execution yields `success=False`
- dry-run does not execute the command

Also required:

- all pre-existing orchestrator tests continue to pass
- `simulate_backlog()` remains available and passing
- `tests/test_project_adapter.py` continues to pass without requiring constructor changes in the test

## Guardrails

- Do not remove simulation mode
- Do not hardcode project-specific behavior in core orchestrator classes
- Do not parse task output here beyond minimal structural normalization
- Do not break backward compatibility in `ProjectConfig`