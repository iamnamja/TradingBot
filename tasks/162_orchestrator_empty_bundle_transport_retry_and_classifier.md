# Task 162 — orchestrator empty bundle transport retry and classifier

## Goal
Harden the bundle transport lane so empty BEGIN_FILE_BUNDLE / END_FILE_BUNDLE responses are classified explicitly, retried with a stronger transport-only re-ask, and surfaced as a distinct failure family when retries are exhausted.

## Why
Live proof-mode runs showed that one-task execution can fail before task logic is exercised because the model returns an empty bundle. That transport failure should not be confused with task failure.

## Requirements
- Detect empty bundle transport separately from general malformed bundle transport.
- Issue one bounded transport-focused retry before hard failure.
- Persist clear diagnostics to the retained runtime artifacts.
- Keep the retry scoped to bundle transport only; do not widen to general task retries.
- Preserve current FILE:/END_FILE contract and known-safe artifact handling.

## Acceptance
- Empty bundle responses are classified distinctly from other bundle failures.
- One bounded transport retry occurs before final failure.
- Runtime artifacts clearly explain whether the final failure was empty-bundle transport.
- Tests cover empty-bundle success-after-retry and exhausted-retry failure.
