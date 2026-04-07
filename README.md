# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized proof checkpoint is now complete through **Task 107** for the post-099 resilience tranche.

The deterministic proof-backed slice currently covers:

- role-separated **controller / builder / verifier** contract
- sequential role loop with controller-owned final continue/stop authority
- dependency-aware short-manifest planning/routing
- explicit verification-authority truth posture
- second-project **Python** portability proof
- truthful external-workspace bootstrap blocked-then-recovered proof
- supervised local-first mixed-manifest re-proof across proof/docs + bootstrap + consumer-facing task families
- extraction-prep consumer boundary posture (not full extraction)

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for authoritative status narrative.

## What the repo can honestly claim today

Today the repo has deterministic local proof for a bounded multi-agent portability, recovery, and supervised mixed-manifest slice:

1. controller/builder/verifier role separation
2. stable sequential role loop
3. planner/routing/verification truth consistency
4. Python-only second-project portability
5. truthful bootstrap blocked-then-recovered handling for a simple external Python workspace
6. supervised mixed-manifest progression bounded by explicit max-task limits
7. conservative stop behavior when verification authority is unsatisfied
8. explicit consumer boundary and extraction-prep posture

It does **not** claim:

- arbitrary project creation for any language or task family
- broad unattended scheduler autonomy
- full standalone extraction completion

## Next continuation target

The next tranche after 107 should convert the current bounded proof into a more durable operating mode for broader ordinary-task autonomy.

That work should focus on:

- explicit coder/tester/controller handoff artifacts
- tester critique bundles and focused replay
- non-repeating repair memory
- safe task admission and decomposition gates
- truthful hosted-check contract and repo probe behavior
- a real multi-role task execution loop rather than only proof-facing role surfaces
- cross-task context carry-forward for bounded backlog execution
- a fresh end-to-end supervised ordinary-manifest autonomy re-proof

## Scope boundary

The current proof remains intentionally narrow:

- short dependency-aware manifests
- deterministic local tests and stubs
- explicit verification-authority constraints
- supervised local-first mixed-manifest execution only
- Python-first portability only
- simple external workspace bootstrap recovery only
- monorepo operation with extraction preparation posture

## Documentation entry points

- `docs/README.md` — docs index and reading order
- `docs/TRADINGBOT_PROJECT_STATE.md` — authoritative current state and tranche boundaries
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md` — product capability and boundary posture
- `docs/ORCHESTRATOR_ROADMAP_100_107.md` — resilience and hosted-authority tranche
- `docs/ORCHESTRATOR_ROADMAP_108_115.md` — autonomy-operating-mode continuation after Task 107
- `tasks/README.md` — canonical numbered task map

## Development

- Lint: `ruff check .`
- Tests: `pytest -q`
