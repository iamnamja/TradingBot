# Task 054 — Orchestrator Package Extraction Prep

## Goal

Prepare the orchestrator for a later clean package/repository extraction without actually splitting the repo yet.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md`
- `README.md`
- `src/builder/orchestrator/__init__.py`
- `tests/test_orchestrator_package_surface.py`
- `docs/orchestrator_extraction_plan.md`

## Harness policy

- FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY
- FILE: docs/TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md MODE=DOCS_ONLY
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

## Canonical docs constraint

Use `docs/` as the canonical home for orchestrator/tradingbot narrative docs.

Do not create or modify root-level `ORCHESTRATOR_*.md` or `TRADINGBOT_*.md` files in this task.
The only root-level markdown file that may be updated here is `README.md`.

## Compatibility constraint

This task should shape an intentional package surface, not break the current public/bootstrap/config contracts that 050–052 stabilized.

In particular, these existing imports/locations must remain available after this task:

- `builder.orchestrator.project_config.ProjectConfig`
- `builder.orchestrator.project_config.GenericProjectConfig`
- `builder.orchestrator.project_config.load_project_config`
- `builder.orchestrator.project_config.bootstrap_project_config_scaffold`
- `builder.orchestrator.project_adapter.ProjectAdapter`
- `builder.orchestrator.project_adapter.load_project_adapter`
- `builder.orchestrator.project_adapter.bootstrap_project_adapter_scaffold`
- `builder.orchestrator.project_adapter.build_bootstrap_starter_docs_text`
- `builder.orchestrator.project_adapter.build_bootstrap_task_template_text`

The package-surface test may validate re-exports through `builder.orchestrator`, but this task must not remove the existing module-level import points above.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- extraction-plan docs are concrete and sequence-aware
- the package-surface test passes without depending on TradingBot-specific imports
- `src/builder/orchestrator/__init__.py` defines an intentional orchestrator package surface rather than a catch-all export pattern
- docs updates for this task land under `docs/`, except for `README.md`
