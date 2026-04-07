# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized proof checkpoint is now complete through **Task 106** for the post-099 resilience tranche.

The deterministic proof-backed slice currently covers:

- role-separated **controller / builder / verifier** contract
- sequential role loop with controller-owned final continue/stop authority
- dependency-aware short-manifest planning/routing
- explicit verification-authority truth posture
- second-project **Python** portability proof
- truthful external-workspace bootstrap blocked-then-recovered proof
- extraction-prep consumer boundary posture (not full extraction)

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for authoritative status narrative.

## What the repo can honestly claim today

Today the repo has deterministic local proof for a bounded multi-agent portability and recovery slice:

1. controller/builder/verifier role separation
2. stable sequential role loop
3. planner/routing/verification truth consistency
4. Python-only second-project portability
5. truthful bootstrap blocked-then-recovered handling for a simple external Python workspace
6. explicit consumer boundary and extraction-prep posture

It does **not** claim:

- arbitrary project creation for any language or task family
- broad unattended scheduler autonomy
- full standalone extraction completion

## Scope boundary

The current proof remains intentionally narrow:

- short dependency-aware manifests
- deterministic local tests and stubs
- explicit verification-authority constraints
- Python-first portability only
- simple external workspace bootstrap recovery only
- monorepo operation with extraction preparation posture

## Documentation entry points

- `docs/README.md` — docs index and reading order
- `docs/TRADINGBOT_PROJECT_STATE.md` — authoritative current state and tranche boundaries
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md` — product capability and boundary posture
- `docs/ORCHESTRATOR_ROADMAP_100_107.md` — resilience and hosted-authority tranche
- `tasks/README.md` — canonical numbered task map

## Development

- Lint: `ruff check .`
- Tests: `pytest -q`
