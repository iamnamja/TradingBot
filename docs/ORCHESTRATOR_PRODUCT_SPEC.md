# Orchestrator Product Spec (In-Repo Productizing Engine)

## Product intent

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, and seam-aware testability.

## Current product stage

- **Post-048 baseline achieved** (042–048 complete)
- **049–054 complete on `main`**
- **Current continuation: 055–061**
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
- Localized repair and protected-method handling for high-risk meta files

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

### Completed stabilization / continuity hardening (049–054)

1. Shell convergence umbrella and dedupe
2. Public interface freeze hardening
3. Documentation/status normalization
4. Portability proof on a second project
5. Stable seam registry
6. Task / seam preflight linter umbrella
7. Meta harness lane gate
8. Bundle preflight / localized repair

### Active continuation (055–061)

9. One seam-aligned integrated capability E2E flow
10. Failure-journal live seam stabilization
11. Safe-parallelism / review integration stabilization
12. Runtime artifact quarantine integration stabilization
13. Extraction prep for future package/repo split
14. Canonical docs path policy
15. Task scope / split heuristics

## Packaging and repo strategy

- **Now**: continue in current repo to complete the continuation and prove seam stability
- **Later**: execute extraction once 055–061 validates seam stability, integrated confidence, packaging readiness, and task-splitting discipline

## Success criteria for extraction readiness

- Stable public interfaces with tested compatibility
- Stable seam registry for orchestrator integration tests
- Preflight can catch common seam/task-shape mistakes early
- Demonstrated portability beyond the primary project
- One integrated E2E flow validated under current live contracts
- Focused seam-family hardening completed
- Documentation/state surfaces synchronized and unambiguous
- Task-splitting and docs-placement policy are explicit
