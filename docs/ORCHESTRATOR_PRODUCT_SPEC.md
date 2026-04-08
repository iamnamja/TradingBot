# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- **124–129** freeze compatibility/public-contract posture and re-prove the bounded supervised portfolio slice
- **130–136** harden convergence around proof-task admission, bundle failure classification, missing-deliverable retry compilation, assertion-to-compatibility repair planning, last-green subset preservation/rollback, hosted-authority operational convergence, and a bounded supervised resilience re-proof
- **137** closes the remaining gap between modeled hosted-authority truth and real GitHub required-check enforcement posture around the stable `ci-required` context
- **138** adds a narrow safe-lane task-family allowlist for one-task admission
- **139** adds a dedicated single-task canary runner with a persisted deterministic run ledger
- Product scope remains bounded and truthful; it is still not claiming broad unattended autonomy

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
- explicit operational-readiness truth that blocks unattended claims when required checks are absent or not reported
- real GitHub enforcement verification showing whether branch rules/protection actually require the configured `ci-required` context on the base branch

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- full standalone extraction is complete

## Next product-stage focus

Continue toward a **safe autonomous single-task lane**:

- allowlisted autonomous task-family admission instead of broad self-hosting autonomy
- explicit classification into `autonomous_safe`, `supervised_only`, or `escalation_required` for one-task runs
- a dedicated single-task runner plus persisted run ledger as the bounded canary execution surface
- canary metrics and recovery reporting layered on top of that ledger
- explicit escalation / handoff artifacts for unsafe self-hosting work
- supervised one-task autonomous proof only after the safe lane is operationally green
