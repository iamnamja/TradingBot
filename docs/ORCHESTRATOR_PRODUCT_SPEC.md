# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- **124–136** hardened the bounded supervised portfolio slice and its failure/authority truth
- **137–148** created and operationally converged the narrow autonomous one-task lane: safe-task-family allowlisting, dedicated runner + ledger, canary reporting, supervised handoff, real GitHub required-check truth, scheduler bridging, stop/requeue policy, resume semantics, and the first operator proof bundle
- the product now has a bounded autonomous one-task capability with a deterministic developer / verifier / repair / controller record, plus a measured external-safe re-proof showing a roughly two-thirds supervised pass-rate band on the current corpus, but not yet broad autonomous app-building capability

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
- operator-visible proof artifacts for the bounded one-task lane

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- arbitrary multi-task autonomous execution
- broad self-hosting control-plane autonomy

## Next product-stage focus

The next product phase should optimize for **execution quality**, not more surface area:

- evaluate the current lane on an external-safe ordinary task corpus
- run a real bounded dev / test / repair / controller loop inside one task
- improve targeted self-heal behavior on ordinary external-safe failures
- measure pass rate, retry rate, escalation rate, and dominant failure classes
- re-prove the one-task lane on that corpus before any two-task widening

Tasks 149–153 now define the canonical external-safe evaluation manifest, wire the bounded one-task runner into a deterministic developer / verifier / repair / controller record, classify ordinary failures into narrower self-heal lanes, measure pass-rate and dominant non-completion reasons, and then re-prove the current claim on that corpus. The current truthful band is roughly **4 completed runs out of 6 corpus items** under supervision, with **2 completed after bounded self-heal** and the remaining failures staying bounded rather than silently widened.

Only after those criteria are met should the product consider bounded two-task trials, and only later should it be wrapped as a separate operator-facing app.
