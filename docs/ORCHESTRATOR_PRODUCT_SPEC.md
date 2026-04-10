# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- **124–129** freeze compatibility/public-contract posture and re-prove the bounded supervised portfolio slice
- **130–136** harden convergence around proof-task admission, bundle failure classification, missing-deliverable retry compilation, assertion-to-compatibility repair planning, last-green subset preservation/rollback, hosted-authority operational convergence, and a bounded supervised resilience re-proof
- **137–146** converge the narrow safe autonomous single-task lane: required-check enforcement probing, safe-task-family allowlisting, one-task runner + ledger, canary reporting, supervised handoff, re-proof, real PR smoke proof, scheduler bridging, and stop/requeue policy for mixed queues
- Product scope remains bounded and truthful; it is still not claiming broad unattended autonomy

## What the product can honestly claim today

The repo has deterministic proof for a bounded supervised portfolio slice plus a narrow one-task autonomous safe lane:

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
- a bounded scheduler bridge that routes exactly one admitted safe task through the dedicated single-task runner and stops/requeues mixed queues conservatively

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- full standalone extraction is complete

## Next product-stage focus

Continue by making the **safe autonomous single-task lane** resumable and idempotent:

- preserve one-task boundedness on resume/re-entry
- avoid duplicate ledger rows and duplicate supervised artifacts after interruption
- keep mixed queues stop/requeue + supervised handoff first
- only move to operator-facing live canary proof once resume semantics are green
