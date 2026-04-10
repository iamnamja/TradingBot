# Task 158 — orchestrator empty bundle transport retry and classifier

## Why

Live proof-mode runs showed a recurring failure where the model returns `BEGIN_FILE_BUNDLE` / `END_FILE_BUNDLE` with no `FILE:` blocks. That is a transport failure, not a task-logic failure, and the runtime should classify, diagnose, and bounded-retry it consistently.

## Scope

Harden empty-bundle transport handling in the bounded one-task runner.

## Requirements

- Distinguish empty-bundle transport failures from generic malformed bundle failures.
- Write an explicit runtime diagnostic artifact when the raw model output is an empty bundle.
- Treat that diagnostic artifact as a known-safe runtime artifact, not an unknown leftover.
- Add a bounded empty-bundle-specific re-ask path before the generic malformed-bundle retry path is used.
- Keep the retry bounded. Do not introduce loops.
- Preserve current bundle parsing rules and public runtime seams.

## Acceptance criteria

- Tests prove that an empty bundle is classified distinctly from other malformed bundle failures.
- Tests prove that an empty bundle triggers one bounded empty-bundle-specific retry prompt before the generic retry prompt.
- Tests prove that repeated empty bundles still terminate and write a diagnostic artifact.
- Tests prove that `_last_agent_file_bundle_error.txt` is classified as a known-safe runtime artifact.
