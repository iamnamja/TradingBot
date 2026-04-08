# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized proof checkpoint is now complete through **Task 136**.

The bounded supervised resilience slice now covers:

- proof-task admission gating on exact deliverable contracts
- empty / underfilled / markerless / malformed bundle classification
- missing-deliverable retry compilation instead of generic retry wording
- coupled compatibility-surface repair planning from assertion evidence
- last-known-good subset preservation during retries
- conservative stop when no dependency-ready tasks are available
- hosted-authority operational convergence truth, including blocking `no checks reported` posture
- green-gated proof-claim discipline

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for the authoritative bounded-scope status narrative.

## What the repo can honestly claim today

Today the repo has deterministic local proof for a bounded supervised multi-project slice plus resilience hardening:

1. controller / builder / verifier role separation
2. project selection across more than one registered project
3. project-scoped workspace, branch, state, and carry-forward isolation
4. dependency-aware next-task choice with conservative stop posture
5. compatibility-preserving hosted-authority and merge-eligibility truth
6. targeted retry planning around missing deliverables and coupled compatibility surfaces
7. bounded subset preservation so retries can roll back only the failing subset
8. explicit operational-convergence truth for hosted authority and unattended-readiness blocking evidence
9. fresh supervised resilience re-proof over the known failure corpus from Tasks 130–135

It does **not** claim:

- broad unattended scheduler autonomy
- arbitrary protected/controller/meta task-family autonomy
- full standalone extraction completion
- arbitrary language portability

## Next continuation target

Complete the real GitHub branch-protection / required-check enforcement around the stable `ci-required` context, then only broaden unattended-readiness claims after that enforcement is truly green.
