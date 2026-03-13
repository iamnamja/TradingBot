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
- `ProjectAdapter.translate_to_orchestrator_behavior()`
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

Create or update these exact files, and every listed existing file must be included in the same bundle:

- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_real_execution.py`
- `tests/test_project_adapter.py`
- `tests/test_multi_project_adapters.py`

## Bundle completeness requirement

The bundle is incomplete unless all seven deliverables are present.

In particular:

- `tests/test_project_adapter.py` must always appear in the bundle
- `tests/test_multi_project_adapters.py` must always appear in the bundle
- `tests/test_orchestrator_real_execution.py` must always appear in the bundle

If the agent changes `project_adapter.py` or `project_config.py`, it must also materially update both adapter-related test files in the same bundle.

If the agent changes `runner.py`, it must materially update `tests/test_orchestrator_real_execution.py` in the same bundle.

## Critical anti-truncation rule

The solution is invalid unless the final `src/builder/orchestrator/runner.py` in the bundle visibly contains all of the following literal method headers:

- `def select_next_task(`
- `def run_next_task(`
- `def execute_task(`
- `def process_execution_result(`
- `def simulate_backlog(`

The solution is also invalid unless `runner.py` visibly contains a final simulation return dictionary with these keys:

- `processed_tasks`
- `stopped_reason`
- `final_status`
- `approval_required`
- `planned_actions`

A partial or truncated `runner.py` is invalid even if the parser accepts the bundle.

## Important CLI relaxation

`src/builder/orchestrator/cli.py` must still be included in the bundle and must remain backward compatible.

However, this task is NOT blocked solely because `cli.py` is unchanged or only minimally changed.

If the actual compatibility fixes are in `runner.py`, `project_config.py`, `project_adapter.py`, and the listed test files, that is sufficient.

Do not force unnecessary churn in `cli.py`.

Including the current compatible `cli.py` in the bundle is acceptable.

## Required behavior

1. Add task-runner configuration to the project config layer.

2. `ProjectConfig` must remain backward compatible:
   - adding `task_runner_command` is allowed
   - it must be optional or have a safe default value
   - existing constructor calls without that field must still work
   - do not make `ProjectConfig` frozen or immutable if existing tests mutate config fields after construction

3. `ProjectAdapter(config=...)` must still work.

4. `ProjectAdapter.translate_to_orchestrator_behavior()` must still exist.

5. `ProjectAdapter.get_tradingbot_default_config()` must still exist.

6. `ProjectAdapter.get_generic_project_config()` must still exist.

7. `OrchestratorRunner.__init__` must keep the existing constructor signature:
   - `config`
   - `backlog_tracker`
   - `initial_state`

8. `OrchestratorRunner.select_next_task()` must still exist.

9. `OrchestratorRunner.simulate_backlog()` must still exist and keep current behavior.

10. `run_next_task(dry_run=True)` must preserve the current dry-run response contract, including existing keys expected by tests.

11. `run_next_task()` when no pending tasks exist must preserve the current no-task response contract, including existing keys expected by tests.

12. `execute_task()` must support two modes:

### Legacy/default mode

If no explicit real task-runner command is configured, preserve the current legacy/mock behavior so existing tests continue to pass.

This means the default path must NOT try to run a subprocess like `default_task_runner`.

This also means tests that exercise the default config path must continue to see the legacy/mock success behavior unless they explicitly opt into real execution mode.

### Real execution mode

If an explicit real task-runner command is configured, `execute_task()` may invoke it and return a structured result.

13. Real execution mode must capture:
   - stdout
   - stderr
   - returncode
   - resolved task file path

14. The real execution result must look like:

{
    "success": bool,
    "status": str,
    "stdout": str,
    "stderr": str,
    "returncode": int,
    "task_file": str
}

## Exact legacy contract that must not be changed

The existing legacy runner contract must be preserved exactly.

When a pending task exists on the legacy/mock success path:

- `task_name == "001_task.py"` for the selected task in existing tests
- `status == "running"`
- `message == "Task is now running."`
- `outcome == "ready_for_pr"`
- `next_action == "merge"`

When review is blocked after a successful task execution:

- `task_name == "001_task.py"`
- `status == "running"`
- `message == "Task is now running."`
- `requires_approval == True`

When no pending task exists:

- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`
- `outcome == "noop"`

A solution is invalid if it changes these legacy values to alternatives such as:

- `status == "succeeded"`
- `message == "Execution succeeded."`

## Exact compatibility rules that must now pass

### Simulation sequencing

When `simulate_backlog()` encounters an approval-blocked task, that task must still be appended to `processed_tasks` before the simulation stops.

Example required behavior:
- task 1 succeeds
- task 2 becomes approval-blocked
- returned `processed_tasks` must be `["001_task.py", "002_task.py"]`

This is mandatory. A solution that returns only `["001_task.py"]` in that scenario is invalid.

### Exact simulation behavior that must be preserved

`simulate_backlog()` must remain implemented and must preserve legacy simulation semantics.

It must return a dictionary with:

- `processed_tasks`
- `stopped_reason`
- `final_status`
- `approval_required`
- `planned_actions`

When `simulate_backlog()` encounters an approval-blocked task, that task must still be appended to `processed_tasks` before the simulation stops.

Example required behavior:
- task 1 succeeds
- task 2 becomes approval-blocked
- returned `processed_tasks` must be `["001_task.py", "002_task.py"]`
- `stopped_reason == "Approval required"`
- `final_status == "blocked"`
- `approval_required == True`

When simulation stops because execution failed:
- `stopped_reason == "Execution failed"`
- `final_status == "failed"`
- `approval_required == False`

A solution is invalid if `simulate_backlog()` skips `run_review(...)` on successful executions.

### Mocked success path

If `execute_task()` returns a mocked success payload with `success=True`, and `changed_files` is empty or missing, existing tests must still reach:

- `outcome == "ready_for_pr"`
- `next_action == "merge"`

Do not default a mocked success path to `review_blocked` merely because `changed_files` is empty or omitted.

If `run_review(...)` is called on a mocked success path where `changed_files` is empty or omitted, preserve the legacy success contract instead of forcing a review-blocked outcome.

### Mocked failure path

If a mocked failure payload does not include `failure_text` but does include `stderr`, preserve the failure message contract expected by tests.

For example:

{
    "success": False,
    "stderr": "Execution failed"
}

must still allow:

- `message == "Execution failed: Execution failed"`

Do not reduce the failure message to a generic `"Execution failed."` when `stderr` already contains the specific error text.

## Exact forbidden fallbacks

The following implementation choices are invalid in this task:

- In `run_review()`, returning `{"mergeable": False}` merely because `changed_files` is empty on a mocked success path
- In `process_execution_result()`, building the failure message only from `failure_text` and ignoring `stderr`
- In `simulate_backlog()`, stopping before appending the approval-blocked task to `processed_tasks`
- In `simulate_backlog()`, not calling `run_review(...)` after successful execution
- In `cli.py`, setting `config.task_runner_command = "default_task_runner"`
- In `cli.py`, inventing any fallback task runner command string when no real command is configured
- In `runner.py`, changing legacy success `status` from `"running"` to `"succeeded"` or similar
- In tests, rewriting legacy expectations away from `"running"` / `"Task is now running."`

### Invalid examples

INVALID:

- breaking out of `simulate_backlog()` after the first approval-blocked task when the required processed sequence is `["001_task.py", "002_task.py"]`
- returning `planned_actions == []` on the fully successful simulation path
- leaving an unused local like `output = execution_result.get("output", "")` in `runner.py`
- `message = "Execution succeeded."` on the legacy success path
- `requires_approval = self.run_review(... )["mergeable"]`
- `if requires_approval:` immediately after assigning `requires_approval = mergeable`
- `if not effective_changed: return {"mergeable": False}`
- `message = f"Execution failed: {failure_text}" if failure_text else "Execution failed."`
- returning from `simulate_backlog()` before appending the current approval-blocked task name
- `config.task_runner_command = "default_task_runner"`
- `return {"status": "succeeded", "message": "Execution succeeded."}` on the legacy success path
- `requires_approval = not changed_files`
- `if execution_result.get("requires_approval"): ...`
- `command = f"{self.config.task_runner_command} {task.name}"`

If `--real-execution` is supported in `cli.py`, it may only enable behavior when a real configured command already exists. It must not invent a command.

## Exact implementation patch guidance for runner.py

The remaining failing cases shown by the current bundle must be fixed directly in `src/builder/orchestrator/runner.py`.

A valid fix should do all of the following:

1. In `run_review(...)`:
   - if `changed_files` is empty or missing on the legacy/mock path, return `{"mergeable": True}`
   - do not block review solely because no changed files were supplied by a mocked execution payload

2. In `process_execution_result(...)` failure handling:
   - set `failure_text = execution_result.get("failure_text") or execution_result.get("stderr") or execution_result.get("output") or ""`
   - then use that resolved text in the returned message

3. In `run_next_task(...)` success handling:
   - preserve `status == "running"`
   - preserve `message == "Task is now running."`
   - do not rename the legacy success state to `"succeeded"`

4. In `simulate_backlog()`:
   - append the current task name to `processed_tasks`
   - call `run_review(...)` after successful execution
   - if review is blocked, set:
     - `stopped_reason = "Approval required"`
     - `final_status = "blocked"`
     - `approval_required = True`
   - if execution fails, set:
     - `stopped_reason = "Execution failed"`
     - `final_status = "failed"`
     - `approval_required = False`

5. In `process_execution_result(...)` success handling:
   - do NOT set `requires_approval` based only on whether `changed_files` is empty
   - `requires_approval` must be derived from the review result, not from empty `changed_files`
   - if `run_review(...)` returns `{"mergeable": True}`, then `requires_approval == False`
   - if `run_review(...)` returns `{"mergeable": False}`, then:
     - `outcome == "review_blocked"`
     - `next_action == "requires_approval"`
     - `requires_approval == True`

6. In `simulate_backlog()`:
   - do not inspect `execution_result.get("requires_approval")`
   - derive approval-blocked simulation behavior from `run_review(...)` or from the processed task result, not from the raw execution payload

7. In `execute_task()` real execution mode:
   - resolve the task file path as `Path(self.config.tasks_directory) / task.name`
   - if invoking Python in tests, pass the resolved task file path, not just `task.name`

8. In `process_execution_result(...)` on the success path:
   - the returned `message` must remain exactly `"Task is now running."`
   - do not return `"Execution succeeded."` on the legacy success path
   - remove unused local variables such as `output` if they are no longer needed

9. In `simulate_backlog()` review handling:
   - `mergeable = self.run_review(...).get("mergeable", True)`
   - approval is required only when `mergeable is False`
   - do not assign `approval_required` from the raw `mergeable` value without inversion
   - when `mergeable is True`, append `f"Task {next_task.name} completed successfully."` to `planned_actions`
   - when `mergeable is False`, append the current task to `processed_tasks`, then stop with:
     - `stopped_reason = "Approval required"`
     - `final_status = "blocked"`
     - `approval_required = True`

10. In `process_execution_result(...)`:
   - if `run_review(...)` returns `{"mergeable": False}`, then:
     - `outcome == "review_blocked"`
     - `next_action == "requires_approval"`
     - `requires_approval == True`
   - if `run_review(...)` returns `{"mergeable": True}`, then:
     - `outcome == "ready_for_pr"`
     - `next_action == "merge"`
     - `requires_approval == False`

11. In `simulate_backlog()` approval-flow compatibility:
   - when the review function is mocked to return `{"mergeable": False}` for the approval scenario tests, the simulation must still satisfy:
     - `processed_tasks == ["001_task.py", "002_task.py"]`
     - `stopped_reason == "Approval required"`
     - `final_status == "blocked"`
     - `approval_required == True`
   - do not stop after only the first task in that scenario

12. In `simulate_backlog()`:
   - preserve success-path planned actions for mergeable tasks:
     - append `f"Task {next_task.name} completed successfully."` to `planned_actions`
   - do not leave `planned_actions` empty on the successful simulation path

13. In `process_execution_result(...)` and related helpers:
   - remove unused local variables such as `output` if they are not used
   - the implementation must pass `ruff` without relying on unsafe fixes

These are the current failing compatibility gaps and must be fixed.


## Real execution test guidance to prevent the next likely failure

`tests/test_orchestrator_real_execution.py` must be updated in a way that is portable and deterministic.

A solution is preferred if it verifies real execution behavior by mocking `subprocess.run` and asserting:

- the subprocess was invoked
- the resolved task file path is `Path(tasks_directory) / task.name`
- stdout/stderr/returncode are normalized correctly
- success/failure mapping is correct

This is preferred because setting only:

`config.task_runner_command = "python"`

and then expecting success from `python tasks/001_task.py` is fragile unless the target task file is guaranteed to be a valid runnable script.

If real-execution tests do not mock `subprocess.run`, they must use a known cross-platform-safe invocation that is guaranteed to succeed in the test environment.

### Additional invalid examples for tests

INVALID:

- `config.task_runner_command = "python"` followed by an assumption that `python tasks/001_task.py` will succeed without mocking
- tests that rely on a task markdown file or backlog task file being executable as a standalone Python program when that is not guaranteed
- tests that use plain `echo` as the subprocess executable

A valid real-execution test should prefer one of these patterns:

- patch `subprocess.run` and assert the resolved path and normalized return structure
- or use a safe Python `-c` based command only if the runner implementation explicitly supports that invocation style


## Exact test mutation constraints

`tests/test_orchestrator_real_execution.py` may add new real-execution coverage, but it must NOT rewrite the existing legacy expectations away from:

- `status == "running"`
- `message == "Task is now running."`

`tests/test_project_adapter.py` and `tests/test_multi_project_adapters.py` must be materially updated, but they must not be changed in a way that weakens or removes the existing compatibility expectations.

## Exact real execution portability rule

Do not use plain `echo` as the subprocess executable in real-execution tests or examples.

A plain command like `echo` is not portable on Windows in this context.

Real-execution coverage must use a cross-platform-safe command, such as a Python invocation using the current interpreter.

A solution is invalid if it introduces or preserves real-execution tests that rely on plain `echo`.

## Ownership and typing constraints

The following ownership rules are mandatory:

- `ProjectConfig` is a data container only.
- Do NOT move `get_tradingbot_default_config()` onto `ProjectConfig`.
- Do NOT move `get_generic_project_config()` onto `ProjectConfig`.
- Those factory methods must remain on `ProjectAdapter`.

The following constructor/API rules are mandatory:

- `ProjectAdapter(config=...)` must continue to work.
- `ProjectAdapter.translate_to_orchestrator_behavior()` must continue to work.
- `OrchestratorRunner(config, backlog_tracker, initial_state)` must continue to work.
- `run_next_task()`, `select_next_task()`, and `simulate_backlog()` must continue to exist.

### Exact config mutability and dataclass rule

Both `ProjectConfig` and any subclass such as `GenericProjectConfig` must remain mutable.

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig`.
Do NOT use `@dataclass(frozen=True)` on `GenericProjectConfig`.
Do NOT mix frozen and non-frozen dataclasses in this module.

The following must continue to work in tests:

`config.task_runner_command = ...`

A solution that makes either config class frozen is invalid.

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
- Do not remove `translate_to_orchestrator_behavior()`.
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

### Exact run_next_task signature rule

`run_next_task` must preserve its existing public signature:

`run_next_task(dry_run=False)`

Do NOT add new required parameters.
Do NOT add new optional parameters such as `real_execution` if callers and tests do not expect them.
Do NOT change CLI wiring to call `run_next_task(..., real_execution=...)`.

If a real-execution mode is needed, derive it from config or preserve it behind existing-compatible interfaces.

A solution that changes the public call shape of `run_next_task()` is invalid.

## Acceptance criteria

Unit tests verify:

- task path resolution works in real execution mode
- a configured real task-runner command can be invoked
- failed command execution yields `success=False`
- dry-run does not execute the command
- `simulate_backlog()` remains implemented and passing
- default config remains mutable enough for tests that assign `config.task_runner_command = ...`

`tests/test_project_adapter.py`, `tests/test_multi_project_adapters.py`, and `tests/test_orchestrator_real_execution.py` must all be materially updated in the same bundle.

A material update means at least one new assertion, changed expectation, or new test case relevant to:

- task-runner configuration
- backward compatibility
- exact legacy runner contract
- adapter behavior translation
- cross-platform real execution behavior
- simulation compatibility
- config mutability compatibility

Re-outputting the same test file or changing whitespace/comments only is insufficient.

Also required:

- all pre-existing orchestrator tests continue to pass
- `simulate_backlog()` remains available and passing
- `translate_to_orchestrator_behavior()` remains available and passing
- `tests/test_project_adapter.py` continues to pass
- `tests/test_multi_project_adapters.py` continues to pass
- `tests/test_orchestrator_real_execution.py` continues to pass

## Guardrails

- Do not remove simulation mode
- Do not hardcode project-specific behavior in core orchestrator classes
- Do not parse task output here beyond minimal structural normalization
- Do not break backward compatibility in `ProjectConfig`
- Do not break backward compatibility in `ProjectAdapter`
- Do not break backward compatibility in `OrchestratorRunner`
- Do not execute a subprocess in the default/legacy path
