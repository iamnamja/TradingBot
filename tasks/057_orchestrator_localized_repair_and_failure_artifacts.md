# Task 057 — Orchestrator Localized Repair and Failure Artifacts

## Goal

Make localized repair the default for small task bundles and guarantee useful failure artifacts every time a run is rejected.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `agents/lib/bundle_parser.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=request_and_parse_bundle TARGET_ANCHOR=def request_and_parse_bundle(
- FILE: tests/test_run_task_runtime_foundations.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY

## Required behavior

When only a subset of files are bad in a small bundle, preserve the good outputs and retry only the bad subset when safe.

Prefer file-local or syntax-local repair before whole-task restart.

Always emit durable failure artifacts that make it clear what the model produced, what was preserved, and why the bad subset was rejected.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q tests/test_run_task_runtime_foundations.py` passes
- the runner can preserve an accepted file while retrying one failing file in a small test/doc bundle
- failure artifacts are always real and usable on rejection
