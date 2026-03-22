# Task 054 — Orchestrator Package Extraction Prep

## Goal

Prepare the orchestrator for a later clean package/repository extraction without actually splitting the repo yet.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `ORCHESTRATOR_PRODUCT_SPEC.md`
- `TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md`
- `README.md`
- `src/builder/orchestrator/__init__.py`
- `tests/test_orchestrator_package_surface.py`
- `docs/orchestrator_extraction_plan.md`

## Required behavior

1. define the intended package-level public import surface for the orchestrator
2. document the extraction plan and sequencing
3. add a smoke test covering the intended package surface
4. do not actually move files to another repository yet

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- extraction-plan docs are concrete and sequence-aware
- the package-surface test passes without depending on TradingBot-specific imports
