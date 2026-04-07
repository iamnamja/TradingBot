# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized proof checkpoint is now complete through **Task 115**.

The deterministic proof-backed slice currently covers:

- role-separated **controller / builder / verifier** contract
- sequential role loop with controller-owned final continue/stop authority
- ordinary-manifest multi-task progression in supervised local-first mode
- tester critique plus focused replay before broader validation where relevant
- repair-memory suppression of repeated no-progress retries
- bounded cross-task carry-forward memory
- conservative stop behavior when authority/admission gates are unsatisfied
- extraction-prep consumer boundary posture (not full extraction)

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for authoritative status narrative.

## What the repo can honestly claim today

Today the repo has deterministic local proof for a bounded supervised ordinary-manifest autonomy slice:

1. controller/builder/verifier role separation
2. truthful combined coder/tester/controller execution surfaces
3. tester critique and focused replay behavior
4. no-progress repair retry suppression
5. bounded carry-forward across short task sequences
6. conservative authority/admission stop gating
7. explicit claim discipline bound to local deterministic tests

It does **not** claim:

- arbitrary project creation for any language or task family
- broad unattended scheduler autonomy
- full standalone extraction completion

## Next continuation target

The next tranche after Task 115 should focus on turning the current bounded ordinary-manifest proof into the first credible multi-project portfolio operating mode.

That work should focus on:

- canonical project registry and per-project contracts
- project-scoped state, branch, and workspace isolation
- backlog intake plus next-task selection policy
- dependency-aware decomposition for larger backlog work
- stronger self-heal with repair-plan ranking and rollback-to-last-green
- project-aware validation matrices and authority profiles
- stronger hosted merge-eligibility truth
- a new supervised bounded multi-project portfolio re-proof
