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
- **116–122 add project registry, project isolation, backlog/dependency policy, bounded repair/rollback posture, and hosted-authority convergence**
- **123 adds a fresh supervised local-first bounded multi-project portfolio scheduler re-proof**
- Product is reusable and increasingly standardized, but **not extracted** as a standalone repo/package.

## What the product can honestly claim today

The repo now has deterministic proof for a bounded supervised slice:

- project selection across more than one registered project
- isolated project workspace/branch/state/carry-forward memory namespaces
- next-task selection that respects explicit dependency truth
- stronger bounded self-heal planning with conservative rollback posture
- project-aware validation and authority evaluation
- conservative stop behavior when merge/authority posture is unsatisfied
- explicit claim discipline that does not exceed tested deterministic local-supervised scope

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- full standalone extraction is complete
