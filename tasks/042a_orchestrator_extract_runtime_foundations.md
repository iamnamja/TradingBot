# Task 042a — Extract Runtime Foundations

## Goal

Extract provider execution, git operations, and local check execution out of `agents/run_task.py` into dedicated modules, with no behavior change.

## Deliverables

Create or update these exact files. Every listed file must appear in the task result overall:

- `agents/lib/provider_client.py`
- `agents/lib/git_ops.py`
- `agents/lib/check_runner.py`
- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`

Important delivery rule for this task:

- `agents/run_task.py` is a protected deliverable satisfied by protected method mode.
- In the normal multi-file bundle, emit only the non-protected deliverables:
  - `agents/lib/provider_client.py`
  - `agents/lib/git_ops.py`
  - `agents/lib/check_runner.py`
  - `tests/test_run_task_runtime_foundations.py`
- Do NOT emit a normal `FILE: agents/run_task.py` block in the multi-file bundle.

All listed files must be materially updated in the same task result.

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=default_provider
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=default_model_for_provider
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=chat_openai
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=chat_anthropic
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=chat
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=run
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=capture
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=capture_result
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=ensure_clean_worktree
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=ensure_branch
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=run_checks
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_runtime_foundations_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Machine-readable contract directives

- ALLOWED_METHODS: agents.run_task default_provider default_model_for_provider chat_openai chat_anthropic chat run capture capture_result ensure_clean_worktree ensure_branch run_checks
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

## Required implementation shape

`agents/run_task.py` must remain the public entrypoint, but the methods listed in the harness policy should become thin delegating wrappers over the extracted modules.

Do NOT replace `main()` in this task.

Do NOT emit a normal full-file `FILE: agents/run_task.py` bundle for the protected file. Protected-file edits for `agents/run_task.py` must be satisfied only through the declared method replacement / append-method policy.

For the normal multi-file bundle, `agents/run_task.py` is explicitly forbidden even though it is a deliverable for the task overall. If you include it there, the attempt is invalid.

Do NOT stub or weaken existing validators or policy checks while performing the extraction.

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
- replacing `main()`
- weakening `_protected_python_semantic_issues`, `validate_static_bundle_contracts`, `validate_imports`, or protected-file machinery
- creating circular imports from the extracted modules back into `agents.run_task`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `run_task.py` behavior is unchanged on the covered paths
- provider/git/check concerns are no longer implemented inline in one monolithic block
