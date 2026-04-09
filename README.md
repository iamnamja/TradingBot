# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized proof checkpoint is now complete through **Task 142**.

The bounded supervised slice plus narrow safe autonomous one-task lane now covers:

- proof-task admission gating on exact deliverable contracts
- empty / underfilled / markerless / malformed bundle classification
- missing-deliverable retry compilation instead of generic retry wording
- coupled compatibility-surface repair planning from assertion evidence
- last-known-good subset preservation during retries
- conservative stop when no dependency-ready tasks are available
- hosted-authority operational convergence truth around the stable `ci-required` contract
- green-gated proof-claim discipline
- safe task-family autonomy allowlisting for ordinary one-task work
- a dedicated autonomous single-task runner with persisted ledger, canary metrics, recovery reporting, and supervised handoff artifacts
- a fresh supervised re-proof that only one allowlisted safe task at a time is autonomous

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for the authoritative bounded-scope status narrative.

## What the repo can honestly claim today

Today the repo has deterministic local proof for a bounded supervised multi-project slice plus a narrow one-task autonomous canary lane:

1. controller / builder / verifier role separation
2. project selection across more than one registered project
3. project-scoped workspace, branch, state, and carry-forward isolation
4. dependency-aware next-task choice with conservative stop posture
5. compatibility-preserving hosted-authority and merge-eligibility truth
6. targeted retry planning around missing deliverables and coupled compatibility surfaces
7. bounded subset preservation so retries can roll back only the failing subset
8. explicit operational-convergence truth for hosted authority and unattended-readiness blocking evidence
9. fresh supervised resilience re-proof over the known failure corpus from Tasks 130–135
10. a bounded autonomous lane that can run one allowlisted safe task at a time with deterministic artifacts and explicit supervised handoff for anything outside that lane

It does **not** claim:

- broad unattended scheduler autonomy
- arbitrary protected/controller/meta task-family autonomy
- full standalone extraction completion
- arbitrary language portability
- broad multi-task autonomy beyond the one-task lane

## Next continuation target

Keep the lane narrow and operationally honest:

- harden live GitHub PR reporting interpretation around the stable `ci-required` context
- smoke-prove required-check convergence on a real PR
- route the scheduler through the bounded single-task runner when exactly one safe task is ready
- keep self-hosting control-plane work escalation-first unless separately proven safe
- only consider widening beyond one-task autonomy after the live canary proof bundle is green
