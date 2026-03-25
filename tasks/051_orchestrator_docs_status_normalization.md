# Task 051 — Orchestrator Docs / Status Normalization

## Goal

Normalize the markdown/docs layer so it reflects the real post-048 baseline and the new 049–054 stabilization tranche, using the canonical docs locations in `docs/`.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `README.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_ROADMAP_032_048.md`
- `docs/ORCHESTRATOR_ROADMAP_049_054.md`
- `docs/ORCHESTRATOR_VISION_AND_CONTROLS.md`
- `docs/TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Harness policy

- FILE: README.md MODE=DOCS_ONLY
- FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY
- FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY
- FILE: docs/ORCHESTRATOR_ROADMAP_032_048.md MODE=DOCS_ONLY
- FILE: docs/ORCHESTRATOR_ROADMAP_049_054.md MODE=DOCS_ONLY
- FILE: docs/ORCHESTRATOR_VISION_AND_CONTROLS.md MODE=DOCS_ONLY
- FILE: docs/TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md MODE=DOCS_ONLY
- FILE: docs/TRADINGBOT_PROJECT_STATE.md MODE=DOCS_ONLY

## Required behavior

1. mark 042–048 complete in the status/roadmap surfaces
2. describe the next stabilization tranche 049–054
3. keep TradingBot status accurate: still manual paper-trading readiness
4. update the repo-separation recommendation to “separate later, after stabilization tranche”
5. keep the orchestrator described as reusable and increasingly productized, but not yet extracted into its own repo/package
6. treat `docs/` as the canonical home for orchestrator/tradingbot narrative docs
7. keep `README.md` at repo root as the root landing page
8. do not rewrite `docs/README.md` in this task unless it is already explicitly required above

## Constraints

This is a docs-only normalization sweep.

Do not use this task to change engine behavior, CLI behavior, or task ordering.

Do not create or modify root-level `ORCHESTRATOR_*.md` or `TRADINGBOT_*.md` files in this task.
The only root-level markdown file that may be updated by this task is `README.md`.

## Acceptance criteria

- docs are internally consistent
- no doc still claims 042–048 is merely upcoming
- the next tranche is named and ordered consistently across files
- no doc claims the orchestrator has already been extracted into its own repository
- the canonical orchestrator/tradingbot narrative docs updated by this task are under `docs/`
- no new root-level orchestrator/tradingbot narrative doc drift is introduced
