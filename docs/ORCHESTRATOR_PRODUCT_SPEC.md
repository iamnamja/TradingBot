# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- **124–129** freeze compatibility/public-contract posture and re-prove the bounded supervised portfolio slice
- **130–136** harden convergence around proof-task admission, bundle failure classification, missing-deliverable retry compilation, assertion-to-compatibility repair planning, last-green subset preservation/rollback, hosted-authority operational convergence, and a bounded supervised resilience re-proof
- **137–142** add the narrow safe autonomous one-task lane: stable `ci-required` contract alignment, allowlisted admission, bounded single-task runner, deterministic ledger/canary/reporting artifacts, supervised handoff lane, and a fresh safe-lane re-proof
- Product scope remains bounded and truthful; it is still not claiming broad unattended autonomy

## What the product can honestly claim today

The repo has deterministic proof for a bounded supervised portfolio slice plus a narrow one-task autonomous lane:

- supervised local-first progression across more than one registered project
- project-scoped workspace/branch/state/carry-forward isolation
- dependency-aware next-task selection with conservative stop when no tasks are ready
- compatibility-preserving hosted-authority and merge-eligibility truth
- green-gated claim discipline for proof-complete wording
- targeted retry prompts around missing deliverables
- coupled compatibility-surface planning from assertion evidence
- last-green subset preservation so retries can roll back only the failing subset
- bounded one-task autonomous execution for allowlisted safe tasks with deterministic ledger, canary reporting, and explicit supervised handoff for out-of-lane work

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- full standalone extraction is complete
- broad multi-task autonomy beyond the one-task lane

## Next product-stage focus

Continue toward an operationally trustworthy **safe autonomous single-task lane**:

- real GitHub settle-window and dual-surface hosted-authority interpretation
- a supervised live-PR smoke proof around `ci-required`
- scheduler routing through the bounded single-task runner for exactly one safe task
- conservative mixed-queue stop/requeue discipline
- idempotent bounded resume/re-entry
- an operator-readable live canary proof bundle before any broader autonomy claim is considered
