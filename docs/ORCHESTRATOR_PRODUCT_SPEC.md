# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- **124–129** freeze compatibility/public-contract posture and re-prove the bounded supervised portfolio slice
- **130–136** harden convergence around proof-task admission, bundle failure classification, missing-deliverable retry compilation, assertion-to-compatibility repair planning, last-green subset preservation/rollback, hosted-authority operational convergence, and a bounded supervised resilience re-proof
- **137–142** establish and re-prove a safe autonomous single-task lane with real required-check truth, an autonomy allowlist, a dedicated one-task runner and ledger, artifact-based canary metrics plus recovery reporting, deterministic supervised handoff artifacts, and a fresh supervised proof that only one allowlisted safe task at a time is autonomous
- Product scope remains bounded and truthful; it is still not claiming broad unattended autonomy

## What the product can honestly claim today

The repo has deterministic proof for a bounded supervised portfolio slice plus a narrow one-task autonomous canary lane:

- supervised local-first progression across more than one registered project
- project-scoped workspace/branch/state/carry-forward isolation
- dependency-aware next-task selection with conservative stop when no tasks are ready
- compatibility-preserving hosted-authority and merge-eligibility truth
- green-gated claim discipline for proof-complete wording
- targeted retry prompts around missing deliverables
- coupled compatibility-surface planning from assertion evidence
- last-green subset preservation so retries can roll back only the failing subset
- explicit operational-readiness truth that blocks unattended claims when required checks are absent or not reported
- a bounded autonomous single-task lane for allowlisted ordinary work only, with deterministic ledger, canary metrics, recovery reporting, and supervised handoff artifacts

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- full standalone extraction is complete
- operational unattended readiness while real GitHub reporting still says `no checks reported` on live PR branches

## Next product-stage focus

Keep the lane narrow and get the real operational blocker out of the way:

- converge live PR reporting plus branch/ruleset enforcement around the stable `ci-required` context
- keep self-hosting control-plane work escalation-first unless separately proven safe
- only widen beyond one-task autonomy after hosted authority is visibly green on real repository workflows
