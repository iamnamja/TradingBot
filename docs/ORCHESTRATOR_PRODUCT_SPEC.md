# Orchestrator Product Spec (In-Repo Productizing Engine)

## Product intent

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, and deterministic result handling.

## Current product stage

- **Post-048 baseline achieved** (042–048 complete).
- **Current stabilization tranche: 049–054**.
- Product is reusable and increasingly standardized, but **not yet extracted** as a standalone repo/package.

## Users and use cases

- Engineering operators running governed task workflows.
- Projects requiring deterministic, policy-constrained automation.
- Multi-project environments where adapter-driven portability matters.

## Core capabilities

- Structured task ingestion and contract parsing.
- Safety harness with protected-file policies and semantic preflight checks.
- Controlled execution shell and command routing.
- Review/compliance/approval gates.
- Backlog state tracking and recovery.
- Audit logging and failure journaling.
- Optional dry-run/simulation and safe parallelism.
- Multi-project adapter support.

## Stabilization roadmap summary

### Completed tranche (042–048)

- Harness modularization umbrella and extracted foundations.
- Parser/policy and semantic preflight extraction.
- Thin run-task shell parity.
- Runtime artifact quarantine.
- Two-phase spec execution and frozen-task mode.
- Failure journal and retry context.
- Project bootstrap adapter.
- Verification plugins.
- Safe parallelism.

### Active tranche (049–054)

1. Shell convergence umbrella and dedupe.
2. Public interface freeze hardening.
3. Documentation/status normalization.
4. Portability proof on a second project.
5. Integrated capabilities end-to-end proof.
6. Extraction prep for future package/repo split.

## Packaging and repo strategy

- **Now**: continue in current repo to complete stabilization and verification.
- **Later**: execute extraction once tranche 049–054 validates portability and interface stability.

## Success criteria for extraction readiness

- Stable public interfaces with tested compatibility.
- Proven shell routing and task execution determinism.
- Demonstrated portability beyond primary project.
- Integrated E2E confidence under current controls/policies.
- Documentation/state surfaces synchronized and unambiguous.
