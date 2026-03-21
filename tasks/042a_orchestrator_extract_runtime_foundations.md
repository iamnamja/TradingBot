# Task 042a — Extract Runtime Foundations

## Goal

Extract provider execution, git operations, and local check execution out of `agents/run_task.py` into dedicated modules, with no behavior change.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/provider_client.py`
- `agents/lib/git_ops.py`
- `agents/lib/check_runner.py`
- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`

All listed files must be materially updated in the same bundle.

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=chat
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=main
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_runtime_foundations_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Machine-readable contract directives

- ALLOWED_METHODS: agents.run_task main chat
- FORBID_CALLS: runner.run runner.run_all_tasks
- RESULT_KEYS: check_runner lint_ok test_ok output_text

## Critical compatibility requirement

This is a no-behavior-change extraction task.

Do NOT change:

- branch naming behavior
- provider/model parameter handling
- retry count
- command execution semantics
- git cleanliness enforcement
- how `ruff`/`pytest` failures are surfaced

## Required extraction targets

Move the following responsibilities out of `agents/run_task.py` into reusable modules:

### `provider_client.py`

- provider/model call wrapper(s)
- response text return path
- provider-specific shelling or dispatch logic

### `git_ops.py`

- current branch detection
- branch creation
- clean-worktree checks
- push-related helpers used by the runner

### `check_runner.py`

- local lint/test execution
- command result normalization
- text summary returned to the runner

## Test requirements

Add deterministic tests that prove:

1. extracted provider client can be imported and called through the runner path
2. extracted git helpers preserve current branch/worktree behavior on the tested paths
3. extracted check runner preserves current summary/result behavior
4. `agents/run_task.py` still works through the same public surface after extraction

## Exact forbidden patterns

- changing external behavior intentionally
- changing CLI/task arguments
- changing retry policy
- changing task-state semantics
- introducing new product features
- touching unrelated orchestrator engine files under `src/builder/orchestrator/`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `run_task.py` behavior is unchanged on the covered paths
- provider/git/check concerns are no longer implemented inline in one monolithic block
