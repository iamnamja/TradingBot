# Task 056 — Orchestrator Failure Journal Live Seam

## Goal

Stabilize and document the current live failure-journal / failure-report seam so tests can rely on a clear public contract instead of inferred internals.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: tests/test_failure_journal.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY

## Required behavior

1. make the failure-journal export/access seam explicit and stable
2. preserve current behavior where possible rather than introducing a broad redesign
3. ensure focused tests use the **live seam** exposed by the repo rather than inventing new aliases
4. document the supported seam in the controls/policies doc

## Compatibility guardrail

Do not break existing run-task routing, shell entrypoints, or 050/052 compatibility surfaces.

If the current repo exposes failure-journal functionality through `_failure_journal_exports()`, keep that shape stable or extend it in a backward-compatible way.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q tests/test_failure_journal.py` passes
- tests no longer rely on a fabricated `"module"` export if the live seam does not expose one
- the supported failure-journal seam is documented in `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
