# Task 031 — Orchestrator Real Task Execution

## Goal

Replace the orchestrator's mocked task execution step with a real execution bridge that invokes the project's task runner against a selected task file.

## Why

Up to task 030, the orchestrator can discover the backlog, simulate execution across real task files, and evaluate review / approval logic. However, `execute_task()` still returns a mocked success payload. The next milestone is to let the orchestrator actually execute one backlog task.

## Scope

Implement a real execution bridge inside the orchestrator that:

- resolves the selected task file path from the configured tasks directory
- invokes the project task runner command for that task
- captures stdout, stderr, and exit code
- returns a normalized execution payload for downstream review / policy / repair logic

## Deliverables

Create or update these exact files:

- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_real_execution.py`

## Required behavior

1. Add task-runner configuration to the project config layer. This must be generic.
2. The project adapter must define a task-runner command template.
3. `OrchestratorRunner.execute_task()` must invoke the configured task runner.
4. The runner must resolve the selected task path using the task name and tasks directory.
5. Dry-run mode must not execute the task runner.
6. Execution must capture stdout, stderr, and return code.

Execution must return a structured dictionary:

```python
{
    "success": bool,
    "status": str,
    "stdout": str,
    "stderr": str,
    "returncode": int,
    "task_file": str,
}


## Acceptance criteria
Unit tests verify:


- task path resolution works
- failed command returns success=False
- dry-run does not execute command



Existing tests must continue to pass.

## Guardrails

- Do not remove simulation mode
- Do not hardcode project-specific behavior
- Do not parse task output here

