# Orchestrator Product Spec (In-Repo Productizing Engine)

## Product intent

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, and seam-aware testability.

## Current product stage

- **Post-048 baseline achieved** (042–048 complete)
- **049–052 complete on `main`**
- **Current continuation: 055–061 reliability / recovery / autonomy tranche followed by 062–068 deferred continuation**
- Product is reusable and increasingly standardized, but **not yet extracted** as a standalone repo/package

## Users and use cases

- Engineering operators running governed task workflows
- Projects requiring deterministic, policy-constrained automation
- Multi-project environments where adapter-driven portability matters
- Repositories that need stable test seams and guarded integrated coverage before extraction

## Core capabilities

- Structured task ingestion and contract parsing
- Safety harness with protected-file policies and semantic preflight checks
- Controlled execution shell and command routing
- Review/compliance/approval gates
- Backlog state tracking and recovery
- Audit logging and failure journaling
- Optional dry-run/simulation and safe parallelism
- Multi-project adapter support
- Stable seam registry for orchestrator integration testing
- Seam-aware preflight checks for task shape and generated bundles

## Sequence summary

### Completed baseline (042–048)

- Harness modularization umbrella and extracted foundations
- Parser/policy and semantic preflight extraction
- Thin run-task shell parity
- Runtime artifact quarantine
- Two-phase spec execution and frozen-task mode
- Failure journal and retry context
- Project bootstrap adapter
- Verification plugins
- Safe parallelism

### Completed stabilization (049–052)

1. Shell convergence umbrella and dedupe
2. Public interface freeze hardening
3. Documentation/status normalization
4. Portability proof on a second project

### Active continuation (053–061)

5. Stable seam registry
6. Task / seam preflight linter
7. One seam-aligned integrated capability E2E flow
8. Failure-journal live seam stabilization
9. Safe-parallelism / review integration stabilization
10. Runtime artifact quarantine integration stabilization
11. Extraction prep for future package/repo split
12. Canonical docs path policy
13. Task scope / split heuristics

## Packaging and repo strategy

- **Now**: continue in current repo to complete the continuation and prove seam stability
- **Later**: execute extraction once 053–061 validates seam stability, preflight discipline, integrated confidence, and packaging readiness

## Success criteria for extraction readiness

- Stable public interfaces with tested compatibility
- Stable seam registry for orchestrator integration tests
- Preflight can catch common seam/task-shape mistakes early
- Demonstrated portability beyond the primary project
- One integrated E2E flow validated under current live contracts
- Focused seam-family hardening completed
- Documentation/state surfaces synchronized and unambiguous


## Bootstrap lane rule

The orchestrator should support both an autonomous task lane and a manual patch lane. The first harness-bootstrap tasks in the reliability/recovery/autonomy tranche use the manual patch lane to avoid self-modification regressions while the stable contract is being frozen.
