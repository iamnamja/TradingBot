# Task 055c — Orchestrator Seam Manifest and Semantic Contract Validator

## Goal

Replace brittle seam heuristics with explicit manifests and semantic validation for seam-heavy tasks.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `agents/lib/task_contracts.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=request_and_parse_bundle TARGET_ANCHOR=def request_and_parse_bundle(
- FILE: tests/test_run_task_runtime_foundations.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY

## Required behavior

Introduce a seam-manifest / semantic-validation layer that can, at minimum:

- validate allowed export keys against a manifest
- distinguish live helpers like `_failure_journal_exports()` from invented aliases like `failure_journal_export`
- distinguish allowed in-process validation seams from truly recursive runner execution
- provide structured preflight reasons that can feed the remediation planner

## Acceptance criteria

- `ruff check .` passes
- `pytest -q tests/test_run_task_runtime_foundations.py` passes
- at least one seam-heavy test scenario is validated semantically rather than with only naive substring checks

## Implementation note

Keep this task additive. Use identifier-aware seam checks and preserve the current public/helper surface of `agents/run_task.py`.
