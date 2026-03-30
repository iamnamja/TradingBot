# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status (post reliability/autonomy tranche)

The reliability/autonomy tranche is complete through **Task 060**.

Continuation is now intentionally resumed under the renumbered active sequence:

- **061** — continuation reset and numbering sync
- **062–068** — deferred continuation implementation tranche (integrated capabilities, live seam/failure journal integration, review integration, quarantine integration, package extraction prep, canonical docs policy, task scope/split heuristics)

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for status narrative.

## Orchestrator extraction preparation (current scope)

Extraction preparation is active, but no repository split has been executed yet.

- The orchestrator package surface is being intentionally shaped at `builder.orchestrator`.
- Existing module-level imports remain stable for compatibility.
- Narrative planning and sequencing for extraction live in:
  - `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
  - `docs/TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md`
  - `docs/orchestrator_extraction_plan.md`

## Documentation entry points

- `docs/README.md` — docs index and reading order
- `docs/TRADINGBOT_PROJECT_STATE.md` — authoritative current state and tranche boundaries
- `docs/ORCHESTRATOR_ROADMAP_049_054.md` — historical roadmap context for 049–054
- `tasks/README.md` — canonical numbered task map (active/deferred alignment)

## Development

- Lint: `ruff check .`
- Tests: `pytest -q`
## Documentation placement

`README.md` is the canonical root-level entrypoint for the repo. Orchestrator and TradingBot narrative documents, product specs, controls/policies docs, and relationship documents should live under `docs/` rather than being duplicated at repo root.
