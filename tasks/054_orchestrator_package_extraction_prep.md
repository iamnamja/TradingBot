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

## Harness policy

- FILE: ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY
- FILE: TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md MODE=DOCS_ONLY
- FILE: README.md MODE=DOCS_ONLY
- FILE: tests/test_orchestrator_package_surface.py MODE=TESTS_ONLY
- FILE: docs/orchestrator_extraction_plan.md MODE=DOCS_ONLY

## Required behavior

1. define the intended package-level public import surface for the orchestrator
2. document the extraction plan and sequencing
3. add a smoke test covering the intended package surface
4. do not actually move files to another repository yet

## Extraction constraints

- the package surface should re-export orchestrator-facing modules only
- do not re-export TradingBot app modules from `builder.orchestrator`
- the extraction plan should be concrete, ordered, and explicitly depend on stabilization work completing first
- this task is preparatory documentation and package-surface shaping, not an actual repo split

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- extraction-plan docs are concrete and sequence-aware
- the package-surface test passes without depending on TradingBot-specific imports
- `src/builder/orchestrator/__init__.py` defines an intentional orchestrator package surface rather than a catch-all export pattern
