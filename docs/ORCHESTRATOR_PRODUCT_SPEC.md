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
- **116–123 establish bounded supervised multi-project portfolio baseline**
- **124–128 harden compatibility contracts, schema aliases, stop vocabulary, assertion-targeted self-heal, and green-gated claim discipline**
- **129 reruns supervised bounded portfolio re-proof after 124–128 without widening scope claims**
- **130–133 harden proof-task admission, bundle-failure classification, missing-deliverable retry compilation, and coupled compatibility-surface planning**

## What the product can honestly claim today

The repo has deterministic proof for a bounded supervised portfolio slice:

- supervised local-first progression across more than one registered project
- project-scoped workspace/branch/state/carry-forward memory isolation
- dependency-aware next-task selection with conservative no-ready-task stop posture
- compatibility-preserving hosted-authority truth and merge-eligibility truth
- green-gated claim discipline for proof-complete wording
- explicit claim discipline that does not exceed tested deterministic scope

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- full standalone extraction is complete

## Next product-stage focus

Continue strengthening reliability and convergence while preserving truthful bounded supervised scope and compatibility guarantees.

The main product gaps now are:

- proof/re-proof tasks can still be under-specified enough to invite empty or zero-delta model responses
- bundle transport failures are still grouped too broadly, which wastes retries
- retries still lean too hard on generic “fix the bundle” reminders instead of missing-deliverable evidence
- localized repair needs a stronger last-known-good preservation contract
- hosted-authority truth exists, but actual repo-check convergence is not yet strong enough for low-babysitting unattended execution
