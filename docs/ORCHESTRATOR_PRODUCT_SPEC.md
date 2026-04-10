# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- **124–129** freeze compatibility/public-contract posture and re-prove the bounded supervised portfolio slice
- **130–136** harden proof-task admission, bundle failure classification, retry compilation, rollback discipline, and hosted-authority operational convergence
- **137–148** converge the narrow safe autonomous single-task lane: enforcement probing, safe-task-family allowlisting, one-task runner + ledger, canary reporting, supervised handoff, real PR smoke proof, scheduler bridging, stop/requeue policy, idempotent re-entry, and the live operator proof bundle

## What the product can honestly claim today

The repo has deterministic proof for a bounded supervised portfolio slice plus a narrow one-task autonomous safe lane:

- supervised local-first progression across more than one registered project
- project-scoped workspace/branch/state/carry-forward isolation
- dependency-aware next-task selection with conservative stop when no tasks are ready
- compatibility-preserving hosted-authority and merge-eligibility truth
- a bounded scheduler path that routes exactly one uniquely ready safe task through the canonical one-task runner
- explicit supervised handoff, durable reporting artifacts, and bounded resume semantics for anything outside or interrupting that lane
- an operator-readable proof bundle for the bounded lane under supervised real-GitHub conditions
