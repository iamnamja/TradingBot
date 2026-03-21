# Task 045 — Structured Failure Journal and Raw Retry Context

## Goal

Persist classified failures, repeated failure fingerprints, raw failure snippets, and chosen remediation paths to improve retries and postmortems.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/failure_journal.py`
- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Current shell / CLI guidance

If tests invoke runner flow through `agents.run_task.main()`, they must target the **current** shell surface.

Specifically:

- Do **not** assume `main(argv)` unless it actually exists
- Do **not** assume legacy flags like `--task` or `--non-interactive` unless they actually exist
- If invoking `main()`, monkeypatch `sys.argv` and use the current positional `task` plus existing optional flags only

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
4. the journal records both recommended next action and chosen remediation path
5. retry context uses only bounded/focused raw failure snippets

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- repeated failure patterns are journaled and reusable
