# Task 051 — Orchestrator Docs / Status Normalization

## Goal

Normalize the markdown/docs layer so it reflects the real post-048 baseline and the new 049–054 stabilization tranche.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `README.md`
- `TRADINGBOT_PROJECT_STATE.md`
- `TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md`
- `ORCHESTRATOR_PRODUCT_SPEC.md`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `ORCHESTRATOR_VISION_AND_CONTROLS.md`
- `ORCHESTRATOR_ROADMAP_032_048.md`
- `ORCHESTRATOR_ROADMAP_049_054.md`

## Harness policy

- FILE: README.md MODE=DOCS_ONLY
- FILE: TRADINGBOT_PROJECT_STATE.md MODE=DOCS_ONLY
- FILE: TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md MODE=DOCS_ONLY
- FILE: ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY
- FILE: ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY
- FILE: ORCHESTRATOR_VISION_AND_CONTROLS.md MODE=DOCS_ONLY
- FILE: ORCHESTRATOR_ROADMAP_032_048.md MODE=DOCS_ONLY
- FILE: ORCHESTRATOR_ROADMAP_049_054.md MODE=DOCS_ONLY

## Required behavior

1. mark 042–048 complete in the status/roadmap surfaces
2. describe the next stabilization tranche 049–054
3. keep TradingBot status accurate: still manual paper-trading readiness
4. update the repo-separation recommendation to “separate later, after stabilization tranche”
5. keep the orchestrator described as reusable and increasingly productized, but not yet extracted into its own repo/package

## Constraints

This is a docs-only normalization sweep.

Do not use this task to change engine behavior, CLI behavior, or task ordering.

## Acceptance criteria

- docs are internally consistent
- no doc still claims 042–048 is merely upcoming
- the next tranche is named and ordered consistently across files
- no doc claims the orchestrator has already been extracted into its own repository
