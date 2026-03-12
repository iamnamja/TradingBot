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

Create or update these exact files, and every listed existing file must be materially updated in the same bundle:

- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_real_execution.py`
- `tests/test_project_adapter.py`
- `tests/test_multi_project_adapters.py`

## Bundle completeness requirement

The bundle is incomplete unless **all seven deliverables** are present.

This task must not be completed with only implementation-file changes.

In particular:

- `tests/test_project_adapter.py` must always appear in the bundle
- `tests/test_multi_project_adapters.py` must always appear in the bundle
- `tests/test_orchestrator_real_execution.py` must always appear in the bundle

If the agent changes `project_adapter.py` or `project_config.py`, it must also materially update both adapter-related test files in the same bundle.

If the agent changes `runner.py`, it must materially update `tests/test_orchestrator_real_execution.py` in the same bundle.

If the agent changes `cli.py`, it must also materially update at least one test file in the same bundle in a way that makes the CLI behavior change understandable and justified.

## Required behavior

1. Add task-runner configuration to the project config layer.

2. `ProjectConfig` must remain backward compatible:
   - adding `task_runner_command` is allowed
   - it must be optional or have a safe default value
   - existing constructor calls without that field must still work
   - do not make `ProjectConfig` frozen/immutable if existing tests mutate config fields after construction

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

## Exact CLI material-change requirement

`src/builder/orchestrator/cli.py` must be materially updated in this task.

A valid CLI material update must do at least one of the following:

- add a real execution-mode option that is actually wired into `OrchestratorRunner.run_next_task(...)`
- add or update real CLI output so execution results from the real execution bridge are surfaced
- update argument parsing so the real execution bridge can be triggered intentionally while preserving existing behavior by default
- update CLI dependency wiring so the runner uses the preserved backward-compatible constructor and execution path explicitly
- change the printed execution summary, exit handling, or mode-selection branch in a way that is directly tied to real task execution support

Invalid `cli.py` updates include:

- import-only changes
- formatting-only edits
- whitespace-only edits
- comment-only edits
- re-emitting the same logic
- touching the file without changing CLI behavior
- adding a flag that is parsed but never used
- renaming variables without changing behavior

The final bundle must include a meaningful behavior change in `src/builder/orchestrator/cli.py`.

### Exact CLI non-stall rule

A `cli.py` change is only valid if a reviewer can point to a changed runtime branch or changed runtime output.

The following are strongly preferred because they are easy to verify as material:

- change printed CLI summary fields
- change CLI exit-code behavior
- add a new parsed option that actually changes runner invocation behavior
- add a simulation or real-execution output branch that changes printed output

If the model is unsure how to materially change `cli.py`, it should prefer changing printed output and/or exit-code behavior in an observable way.

## Exact test alignment for CLI

At least one updated test or assertion in the bundle must indirectly validate the new CLI-related behavior, execution-mode wiring, or CLI-visible output contract.

It is acceptable for this validation to live in one of these files:

- `tests/test_orchestrator_real_execution.py`
- `tests/test_project_adapter.py`
- `tests/test_multi_project_adapters.py`

But the bundle must make the `cli.py` material change understandable and justified.

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
- CLI wiring or CLI-visible behavior related to real execution or dry-run routing
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
- `src/builder/orchestrator/cli.py` is materially updated with a real behavior-preserving CLI-path change tied to real task execution flow

## Normative compatibility examples

### Exact method preservation

The following methods must remain implemented and callable:

- `ProjectAdapter.translate_to_orchestrator_behavior()`
- `OrchestratorRunner.select_next_task()`
- `OrchestratorRunner.run_next_task(dry_run=False)`
- `OrchestratorRunner.simulate_backlog()`

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

When no pending task exists:

- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`
- `outcome == "noop"`

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

### Exact simulate_backlog implementation requirement

The solution is invalid unless `src/builder/orchestrator/runner.py` contains a literal `def simulate_backlog(` method in the final bundle.

It must not merely mention simulation in comments or docs.

It must be actual executable code in `runner.py`.

### Exact legacy success-path compatibility

If `execute_task()` returns a mocked success payload with `success=True`, existing success-path tests must still be able to reach:

- `outcome == "ready_for_pr"`
- `next_action == "merge"`

Do not default a mocked success path to `review_blocked` merely because `changed_files` is empty or omitted.

If the implementation needs changed files for review logic, preserve backward compatibility for legacy/mock test payloads.

If `run_review(...)` is called on a mocked success path where `changed_files` is empty or omitted, preserve the legacy success contract instead of forcing a review-blocked outcome.

### Exact failure-message compatibility

If a mocked failure payload does not include `failure_text` but does include `stderr`, preserve the failure message contract expected by tests.

For example, a failure payload like:

{
    "success": False,
    "stderr": "Execution failed"
}

must still allow:

- `message == "Execution failed: Execution failed"`

Do not reduce the failure message to a generic `"Execution failed."` when a specific error string is already available in `stderr`.

### Exact runner completeness requirement

The bundle is not acceptable unless `src/builder/orchestrator/runner.py` contains the full final implementation.

A partial or truncated `runner.py` is invalid even if the bundle parses.

In particular, the final `runner.py` must include:

- `select_next_task()`
- `run_next_task(...)`
- `simulate_backlog()`
- the full `process_execution_result(...)` implementation
- the full failure-path return logic

Do not leave `runner.py` ending early after helper calls or with missing return logic.

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

### Exact default-vs-real test separation rule

`tests/test_orchestrator_real_execution.py` must explicitly separate:

- legacy/default-mode expectations when `task_runner_command is None`
- real-execution expectations when `task_runner_command` is explicitly configured

A test that expects subprocess failure must explicitly opt into real execution mode.

A test that uses the default config path must not expect subprocess execution when `task_runner_command is None`.

### Exact simulation preservation rule

The generated solution is not acceptable unless `simulate_backlog()` remains implemented and passing.

Do not replace the runner with a reduced implementation that omits simulation behavior.

### Exact config mutability rule

Existing tests may assign to `config.task_runner_command` after construction.

Do not make `ProjectConfig` immutable or frozen in a way that breaks:

`config.task_runner_command = ...`

### Exact real execution test portability rule

`tests/test_orchestrator_real_execution.py` must be materially updated to avoid plain `echo`.

The real execution test must use a cross-platform-safe command, such as invoking the current Python interpreter with a short `-c` command.

Do not use plain `echo` as the subprocess executable on Windows.

### Exact real command invocation rule

If the real execution test uses Python, the configured command must be represented in a subprocess-safe way.

Do not pass a full shell string like:

`python -c 'print("Hello World")'`

as a single executable token.

Use a command form that is safe for `subprocess.run(...)`, such as a list of executable plus arguments, or another implementation that correctly splits command arguments cross-platform.

## Guardrails

- Do not remove simulation mode
- Do not hardcode project-specific behavior in core orchestrator classes
- Do not parse task output here beyond minimal structural normalization
- Do not break backward compatibility in `ProjectConfig`
- Do not break backward compatibility in `ProjectAdapter`
- Do not break backward compatibility in `OrchestratorRunner`
- Do not execute a subprocess in the default/legacy path
