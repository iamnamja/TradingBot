# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- **090–099 complete:** synchronized multi-agent contract + portability proof + extraction-prep boundary posture
- Product is reusable and increasingly standardized, but still **not extracted** as a standalone repo/package.

## What the product can honestly claim today

The repo now has deterministic proof for:

- role separation across `controller`, `builder`, and `verifier`
- sequential multi-agent loop with controller-owned final decision authority
- dependency-aware short-manifest planning/routing
- explicit verification-authority posture in decision truth
- second-project Python portability proof for a simple generic Python workspace
- explicit monorepo consumer-boundary snapshot as extraction preparation, not completed extraction

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- full standalone extraction is complete

## What the next product step needs to solve

The next product step is not “more features first.” It is **resilience against contract drift**.

The main remaining gaps are now:

- public-surface compatibility is still too brittle for proof-facing helpers
- collection-time import errors are not yet a first-class repair lane
- docs/proof-sync drift is not validated early enough
- hosted required-check authority is not yet proven strongly enough in real branch flows
- result-shape and manifest-schema drift still cause avoidable failures
- repair planning still needs to prefer smaller targeted compatibility patches more consistently

## Next product target after 099

The next product step should harden the orchestrator against proof-sync and public-contract drift before making broader autonomy claims.

This tranche should focus on:

1. public-surface freeze and compatibility aliases
2. collection-error/import-error repair routing
3. proof-sync contract validation and claim guards
4. real hosted CI authority integration
5. result-shape and manifest-schema normalization
6. targeted minimal-patch repair planning
7. external bootstrap recovery proof
8. supervised mixed-manifest autonomy re-proof

## Boundary and claim discipline

Public claims in docs/README must remain narrower than or equal to deterministic proof tests. This remains in force for the post-099 resilience tranche.
