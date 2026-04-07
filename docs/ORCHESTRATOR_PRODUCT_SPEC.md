# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- **Post-048 baseline achieved** (042–048 complete)
- **049–052 complete on `main`**
- **Reliability/autonomy continuation complete through 067** (including 065a and 067a)
- **Protected/controller stabilization complete through 069** (including 068, 068a, 068b, and 068c)
- **070–081 add manifest queue/state/execution/final-acceptance/resume/controller decomposition**
- **082–089 add and harden first autonomous short-manifest proof**
- **090–099 synchronize multi-agent contract + portability proof + extraction-prep boundary posture**
- **100–107 harden resilience, hosted-authority truth, bootstrap recovery, and supervised mixed-manifest proof**
- **108–114 harden ordinary-task autonomy operating mode (artifact envelopes, tester critique/replay, repair memory, admission gates, authority contracts, multi-role ordinary execution, cross-task carry-forward)**
- **115 adds a fresh supervised local-first ordinary-manifest end-to-end re-proof**
- **116 adds a canonical project registry and per-project contract surface for the monorepo plus a generic external Python project**
- Product is reusable and increasingly standardized, but **not extracted** as a standalone repo/package.

## What the product can honestly claim today

The repo now has deterministic proof for a bounded supervised slice:

- short ordinary-manifest progression across multiple ordinary tasks
- combined builder/verifier/controller execution surfaces
- tester critique with focused replay lane before broader validation
- repair-memory suppression of repeated no-progress retries
- bounded cross-task carry-forward memory
- conservative authority/admission gate stop posture
- explicit claim discipline that does not exceed tested deterministic scope

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- full standalone extraction is complete

## Next product-stage focus

The next continuation after Task 116 should focus on converting the new canonical project-registry surface into stronger isolated portfolio execution.

The main product gaps are:

- insufficient project-scoped isolation for state, branches, and workspaces
- weak next-task selection across a real backlog
- dependency and decomposition planning that is still too manifest-shaped
- self-heal that still needs stronger repair-plan ranking and rollback behavior
- validation and authority that are not yet fully project-aware
- hosted authority that is still truthful but not yet operationally converged enough for low-babysitting portfolio execution
