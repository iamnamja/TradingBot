# Task 059 — Orchestrator CI / PR / Merge Controller

## Goal

Make PR creation, CI polling/classification, merge, and resync part of the orchestrator’s native control loop.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/pr_manager.py`
- `src/builder/orchestrator/ci_manager.py`
- `tests/test_orchestrator_pr_creation_workflow.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: tests/test_orchestrator_pr_creation_workflow.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY

## Required behavior

Represent PR/CI/merge as explicit controller states rather than shell snippets around the orchestrator.

At minimum, the controller should know how to:

- create/open a PR
- classify CI status
- merge when safe
- resync `main`
- unlock the next task

The controller should also surface CI failures back into the remediation planner instead of treating them as out-of-band operator work.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- docs describe PR/CI/merge as controller behavior rather than only manual operator workflow
