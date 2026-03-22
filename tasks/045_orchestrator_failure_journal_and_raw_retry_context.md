# Task 045 — Structured Failure Journal and Raw Retry Context

## Goal

Persist classified failures, repeated failure fingerprints, raw failure snippets, and chosen remediation paths to improve retries and postmortems.

Continue shrinking `agents/run_task.py` by extracting failure-journaling logic into `agents/lib/failure_journal.py`.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/failure_journal.py`
- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=_report_failure
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_failure_journal_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Scope guardrail — keep this task narrow

This task is **only** about failure journaling.

Do **not** broaden the shell or re-wrap unrelated runtime-foundations helpers.

Specifically in `agents/run_task.py`:

- do **not** add, delete, rename, or rewrite wrappers for:
  - `default_provider`
  - `default_model_for_provider`
  - `chat_openai`
  - `chat_anthropic`
  - `chat`
  - `run`
  - `capture`
  - `capture_result`
  - `ensure_clean_worktree`
  - `ensure_branch`
  - `run_checks`
- do **not** add, remove, rename, or move these existing runtime-foundations compatibility locals:
  - `_default_provider_local`
  - `_default_model_for_provider_local`
  - `_chat_openai_local`
  - `_chat_anthropic_local`
  - `_chat_local`
  - `_run_local`
  - `_capture_local`
  - `_capture_result_local`
  - `_ensure_clean_worktree_local`
  - `_ensure_branch_local`
  - `_run_checks_local`
- do **not** add duplicate redefinitions of any existing runtime-foundations wrapper function
- do **not** add, remove, rename, move, or rewrite `_runtime_foundations_exports()` in this task
- do **not** change existing provider, git, or check-runner delegation seams in this task
- do **not** convert this task into broader runtime-foundations compatibility work
- only replace `_report_failure(...)` and add `_failure_journal_exports()` additively before the existing `if __name__ == "__main__":` anchor

If you need any failure-journal helper behavior, route it through the new `agents.lib.failure_journal` module and the new additive `_failure_journal_exports()` seam only.

## Hard compatibility reminder

`agents/run_task.py` already contains established runtime-foundations compatibility surfaces from prior tasks.
Those surfaces are **read-only for Task 045**.

If your solution touches or rewrites:

- the existing runtime-foundations locals block,
- the existing `_runtime_foundations_exports()` block,
- or any existing wrapper function bodies named above,

then your solution is wrong for this task.

## Delegation seam requirement

`agents.run_task._report_failure(...)` must resolve its classification, fingerprinting, snippet bounding, next-action recommendation, remediation-path selection, and append behavior through `_failure_journal_exports()` at runtime.

The export seam must be patchable from tests.

Acceptable patterns:

- `_failure_journal_exports()` returns a stable mutable export mapping cached at module scope, or
- tests monkeypatch `agents.run_task._failure_journal_exports` itself and `_report_failure(...)` uses that seam directly

Avoid an implementation where tests mutate one returned export dict but `_report_failure(...)` calls a fresh unrelated dict on every invocation.

## Current shell / CLI guidance

If tests invoke runner flow through `agents.run_task.main()`, they must target the **current** shell surface.

Specifically:

- Do **not** assume `main(argv)` unless it actually exists
- Do **not** assume legacy flags like `--task` or `--non-interactive` unless they actually exist
- If invoking `main()`, monkeypatch `sys.argv` and use the current positional `task` plus existing optional flags only
- Do **not** bypass the live shell seam by editing unrelated globals when a direct export seam exists

## Test import / bootstrap guidance

The repo test environment may not treat `agents` as an installed package during collection.

Therefore generated tests must **not** assume that `from agents.lib import ...` works at top level during pytest collection unless the test first bootstraps repo-root importability explicitly.

Prefer one of these safe patterns:

- import `agents.run_task` with `importlib.import_module(...)` after ensuring repo root is on `sys.path`, or
- load the target helper module via importlib using a file path, or
- import through an already-imported `agents.run_task` export seam

Do **not** add a new top-level test import that can fail collection with `ModuleNotFoundError: No module named 'agents'`.

## Bundle transport safety requirement

Raw failure snippets may contain bundle-marker strings or method-insertion markers.

When generated tests need fixture content containing literals such as:

- `BEGIN_FILE_BUNDLE`
- `FILE:`
- `END_FILE`
- `END_FILE_BUNDLE`
- `BEGIN_METHOD_INSERTION`
- `BEGIN_METHOD`
- `END_METHOD`
- `END_METHOD_INSERTION`

do **not** place those raw marker strings at the start of a source line inside generated file content.

Use split tokens or concatenation instead.

## Required behavior

The failure journal must record at least:

- task identifier
- failure category
- retry count
- failure fingerprint
- bounded raw failure snippet
- recommended next action
- chosen remediation path

The retry loop may use the raw snippet in the next retry context, but should keep it bounded and focused.

## Test requirements

Add deterministic tests that validate:

1. repeated failure patterns are fingerprinted and journaled
2. raw failure snippets remain bounded
3. bundle-marker-like failure snippets do not break generated tests or transport
4. `agents.run_task._report_failure(...)` delegates through the live `_failure_journal_exports()` seam
5. the journal records both recommended next action and chosen remediation path

Generated tests must not require rewriting or bypassing the current runtime-foundations shell wrappers.

## Compatibility requirements

The following existing tests must remain green **without modification of their intent**:

- `tests/test_run_task_runtime_foundations.py`
- `tests/test_run_task_shell_parity.py`
- `tests/test_execution_mode_frozen_task.py`

In particular:

- do not break current runtime-foundations exports
- do not break current shell wrapper delegation
- do not change existing 044 spec/execution behavior
- do not change the current `main()` argument surface

## Implementation note

Keep `agents/run_task.py` as a thin shell.

The actual journaling logic should live in `agents/lib/failure_journal.py`.

`_report_failure(...)` in `agents/run_task.py` should stay small and delegate through `_failure_journal_exports()`.
