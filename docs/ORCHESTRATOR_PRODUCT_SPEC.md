# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- **124–136** hardened the bounded supervised portfolio slice and its failure/authority truth
- **137–148** created and operationally converged the narrow autonomous one-task lane: safe-task-family allowlisting, dedicated runner + ledger, canary reporting, supervised handoff, real GitHub required-check truth, scheduler bridging, stop/requeue policy, resume semantics, and the first operator proof bundle
- **149–154** shifted the product into one-task execution quality: external-safe eval manifest, bounded dev / test / repair / controller loop, external-safe failure taxonomy, scoreboarding and recovery artifacts, corpus re-proof, and the explicit go / no-go gate for any bounded two-task widening

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
- explicit operational-readiness truth around the stable `ci-required` contract
- a bounded scheduler bridge that routes exactly one admitted safe task through the dedicated single-task runner and stops/requeues mixed queues conservatively
- operator-visible one-task evidence: ledger, canary metrics, recovery report, failure taxonomy, failure digest, and external-safe re-proof
- a machine-readable widening gate that decides whether bounded two-task trials are justified

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- arbitrary multi-task autonomous execution
- broad self-hosting control-plane autonomy
- bounded two-task execution readiness as a current fact

## Current widening posture

The product now has an explicit gate for bounded two-task trials. That gate requires all of the following before widening begins:

- at least **6** evaluated one-task external-safe runs
- at least **0.75** completion rate
- at most **0.25** escalation rate
- at most **0.10** hosted-authority block rate
- at most **0.34** self-healed completion share
- direct completions must exceed self-healed completions

The current truthful result is still **no-go**. The present re-proof band remains roughly **4 of 6** completed, with **2 of 4** completions still requiring bounded self-heal.

## Next product-stage focus

The next product work should stay inside one-task execution quality:

- raise direct one-task completion rate
- reduce escalation-required outcomes
- reduce authority-block frequency where possible without weakening truthfulness
- make direct completions clearly outnumber self-healed completions
- keep the lane width at one until the explicit gate clears
