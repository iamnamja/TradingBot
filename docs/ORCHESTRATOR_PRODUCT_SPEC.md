# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- **124–129** freeze compatibility/public-contract posture and re-prove the bounded supervised portfolio slice
- **130–136** harden convergence around proof-task admission, bundle failure classification, missing-deliverable retry compilation, assertion-to-compatibility repair planning, last-green subset preservation/rollback, hosted-authority operational convergence, and the supervised resilience re-proof
- Product scope remains bounded and truthful; it is not yet claiming unattended broad autonomy

## What the product can honestly claim today

The repo has deterministic proof for a bounded supervised portfolio slice plus convergence hardening:

- supervised local-first progression across more than one registered project
- project-scoped workspace/branch/state/carry-forward isolation
- dependency-aware next-task selection with conservative stop when no tasks are ready
- compatibility-preserving hosted-authority and merge-eligibility truth
- green-gated claim discipline for proof-complete wording
- targeted retry prompts around missing deliverables
- coupled compatibility-surface planning from assertion evidence
- last-green subset preservation so retries can roll back only the failing subset
- a fresh bounded supervised resilience re-proof over the concrete known failure corpus

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- full standalone extraction is complete

## Next product-stage focus

Continue toward:

- real hosted required-check / branch-protection convergence is now modeled and check-name aligned (`ci-required`)
- keep the real GitHub required-check / branch-protection alignment synchronized to the stable `ci-required` contract
- claim stronger unattended readiness only after GitHub-side enforcement and a broader supervised proof both stay green
