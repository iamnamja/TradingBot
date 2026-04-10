# Task 158 — orchestrator empty bundle transport retry and classifier

## Why

Live proof-mode runs showed a recurring failure where the model returns `BEGIN_FILE_BUNDLE` / `END_FILE_BUNDLE` with no `FILE:` blocks. That is not a task-logic failure. It is a transport/format failure and should be classified, surfaced, and retried consistently.

## Scope

Harden bundle transport handling for empty-bundle responses.

## Requirements

- Distinguish empty-bundle transport failures from general malformed bundle failures.
- Persist explicit diagnostic artifacts when the raw model output is an empty bundle.
- Add a bounded retry or re-ask path specifically for empty-bundle transport before the run is recorded as failed.
- Preserve existing compatibility seams and bundle parsing rules.
- Ensure the resulting diagnostics are treated as known-safe runtime artifacts, not mysterious leftovers.

## Acceptance criteria

- Tests prove that an empty bundle is classified distinctly from other malformed bundle failures.
- Tests prove that the runtime writes a clear diagnostic artifact for empty-bundle transport failures.
- Tests prove that the retry/re-ask path is bounded and does not loop indefinitely.
- Docs/state files explain that empty bundle is now treated as a first-class transport failure family.
