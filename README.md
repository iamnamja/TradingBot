# TradingBot + Orchestrator

This repository currently contains two tightly related systems:

- **TradingBot**: a manual, paper-trading-oriented execution stack.
- **Orchestrator**: a reusable task-execution and stabilization engine used to implement and harden development workflows.

## Current status (normalized through Task 051)

- The **042–048 orchestrator tranche is complete**.
- The **next stabilization tranche is 049–054** and is now the active roadmap focus.
- TradingBot remains at **manual paper-trading readiness** (not autonomous live-trading production).
- The orchestrator is increasingly productized and reusable, but **has not yet been extracted** into a separate repository/package.
- Repo separation is recommended **later, after the 049–054 stabilization tranche**.

## Canonical documentation location

Narrative status/spec/roadmap documentation for both systems is canonical under:

- `docs/`

Use the root `README.md` as a landing page and index, while treating `docs/` as the source of truth for orchestrator/tradingbot narrative state.

## Key docs

- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_VISION_AND_CONTROLS.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/ORCHESTRATOR_ROADMAP_032_048.md`
- `docs/ORCHESTRATOR_ROADMAP_049_054.md`

## Code layout

- `src/tradingbot/` — TradingBot runtime, strategy, risk, execution, and paper-cycle entrypoints.
- `src/builder/orchestrator/` — orchestrator engine and workflow modules.
- `agents/` — run-task shell, harness components, and support libraries.
- `tests/` — end-to-end and unit/integration coverage across both systems.
- `tasks/` — implementation task specifications and tranche sequencing.
