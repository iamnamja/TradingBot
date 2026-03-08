# Task 027: Orchestrator execute-task workflow

## Goal
Wire the existing orchestrator components into a real single-task execution workflow.

This task should move the orchestrator from “can select a task” to “can run one task workflow end to end in a controlled way.”

## Deliverables
You must create or update all of the following in the same change:
- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_execute_workflow.py`

If any one of these three files is not changed, the task is incomplete.

## Existing repo dependencies (NOT deliverables)
Reuse existing orchestrator modules rather than recreating them:
- `state.py`
- `backlog.py`
- `review.py`
- `failures.py`
- `merge.py`
- `repair.py`
- `policy.py`
- `audit.py`
- `project_config.py`
- `project_adapter.py`

Do not recreate these modules unless a minimal modification is truly required.

## Scope
Implement a **single-task workflow**, not a forever loop.

That means:
- pick one next task
- execute the task workflow once
- return a structured result
- stop

## Repository fact you must respect
Current tests instantiate the runner with:
- `ProjectAdapter.get_tradingbot_default_config()`

That `ProjectConfig` does **not** define `audit_path`.

This is the most important rule in the task:
- the implementation must work cleanly with that existing config object
- the implementation must not assume `config.audit_path` exists

## Backward-compatibility requirements
This task extends the orchestrator runner built in earlier tasks and must preserve existing contracts unless this task explicitly adds fields.

### Existing no-task contract
If no pending task exists in normal mode, `run_next_task()` must continue to return at least:
- `task_name = "none"`
- `status = "no_task"`
- `message = "No pending tasks available."`

### Existing dry-run no-task contract
If no pending task exists in dry-run mode, `run_next_task(dry_run=True)` must continue to return at least:
- `task_name = "none"`
- `status = "no_task"`
- `dry_run = True`

### Existing normal pending-task contract
If a pending task exists in normal mode, existing tests may still expect:
- `task_name` to be the selected task name
- `status = "running"`
- `message = "Task is now running."`

Do **not** silently replace that immediate status/message with review-stage messaging.

## Two-stage result model
The runner now needs to support workflow information **without breaking the immediate runner contract**.

Required pattern:
- keep the immediate runner fields compatible:
  - `task_name`
  - `status = "running"`
  - `message = "Task is now running."`
- add separate workflow fields:
  - `outcome`
  - `next_action`
  - `requires_approval`

## Required workflow
The workflow should do all of the following in order:

1. determine the next pending task
2. represent the task as running
3. invoke the task execution step through an injected collaborator or command wrapper
4. inspect the execution result
5. if successful:
   - run review/compliance evaluation
   - apply policy
   - decide whether the result is mergeable or requires approval
6. if unsuccessful:
   - run failure classification
   - run repair decision logic
7. optionally write audit events for major decisions
8. return a structured orchestration result

## Execution contract
The runner must **not** directly shell out to hardcoded commands inside business logic.
Instead, inject or wrap the execution step so tests can simulate:
- success
- failure
- review blocker
- approval-required outcome

## Audit integration contract
Audit logging must be treated as optional/configurable.

### Forbidden assumptions
Do **not** assume:
- `ProjectConfig.audit_path` exists
- `tasks_directory` is a valid log file path
- empty string `""` is a valid log file path

### Required behavior
If no explicit audit sink/path is configured, the workflow must still run successfully.

Acceptable approaches:
- skip audit writes when no audit path is configured
- inject an audit callback/writer
- guard every audit write behind an explicit configured file-path check

### Explicit implementation rule
The implementation must not call audit helpers with:
- `self.config.audit_path`
- `self.config.tasks_directory`
- `""`

If helper methods such as `process_execution_result()` or `_handle_success()` exist, they must also obey this rule.

A good implementation pattern is:
- centralize optional audit behind a small helper like `_maybe_audit(...)`
- that helper should no-op when no valid audit sink/path exists

## CLI deliverable requirement
`src/builder/orchestrator/cli.py` must be updated in a visible way for this task.

Required CLI change:
- add support for a single-run execute mode that calls the updated runner workflow once
- print a concise summary that includes:
  - `task_name`
  - `status`
  - `outcome`

## Test deliverable requirement
`tests/test_orchestrator_execute_workflow.py` must be created or updated and must contain tests for at least:
- no pending task
- no pending task in dry-run
- execution success + review success
- execution success + review blocked
- execution failure + classified repair action

The test file must be materially updated; a placeholder file is not acceptable.

## Default success-path expectations
The default happy-path test should succeed **without** requiring the test to patch review as mergeable.

That means the task implementation/tests should align so that:
- the default execution result for the happy path produces changed files that are acceptable to the review checker
- the default workflow outcome for the basic success test is:
  - `outcome = "ready_for_pr"`

## Failure message contract
If execution fails and classification/repair logic produces a human-review path, the returned `message` must still preserve the underlying failure text when available.

Example:
- failure text = `"Execution failed"`
- returned message should include `"Execution failed"`

## Structured result contract
Workflow results must use deterministic primitive fields only.

Required fields:
- `task_name: str`
- `status: str`
- `message: str`
- `outcome: str`
- `next_action: str`
- `requires_approval: bool`

## No-task contract
If no pending task exists, return a deterministic no-op result that includes:
- `task_name = "none"`
- `status = "no_task"`
- `outcome = "noop"`
- `next_action = "none"`
- `requires_approval = False`
- `message = "No pending tasks available."`

In dry-run no-task mode, also include:
- `dry_run = True`

## Success-path contract
If task execution succeeds and review/policy allow progress:
- `status = "running"`
- `message = "Task is now running."`
- `outcome = "ready_for_pr"`
- `next_action` is deterministic
- `requires_approval = False`

## Review-blocked contract
If execution succeeds but review blocks:
- `status = "running"`
- `message = "Task is now running."`
- `outcome = "review_blocked"`
- `next_action` reflects review or approval handling
- `requires_approval = True`

## Failure-path contract
If task execution fails:
- use the classifier output
- use repair decision output
- preserve original failure text in `message`
- return deterministic fields reflecting the chosen next action

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- `src/builder/orchestrator/runner.py` is updated consistently, including helper methods
- `src/builder/orchestrator/cli.py` is updated with the execute-once summary behavior
- `tests/test_orchestrator_execute_workflow.py` is created/updated with the required cases
- implementation preserves the previously established runner contracts listed above
- implementation works with `ProjectAdapter.get_tradingbot_default_config()` without attribute errors
- implementation does not treat `tasks_directory` or `""` as an audit log file path
