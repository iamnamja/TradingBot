# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 124–148 are complete in bounded supervised scope:** the repo now freezes public/tested compatibility surfaces, normalizes schema aliases and canonical stop vocabulary, targets assertion-shaped failures toward coupled compatibility surfaces, gates proof tasks on exact deliverable contracts, distinguishes empty/underfilled/markerless/malformed bundle failures, compiles targeted retry prompts around missing deliverables, preserves the last-known-good subset while rolling back only the failing subset during retries, keeps hosted-authority operational convergence truth explicit, verifies real GitHub required-check enforcement convergence around the stable `ci-required` context, establishes a safe task-family autonomy allowlist, adds a bounded autonomous single-task runner with ledger/reporting/handoff/resume semantics, routes the scheduler through that runner when exactly one safe task is ready, applies conservative stop/requeue policy for mixed queues, and packages the current lane into an operator-readable live canary proof bundle.

The current bounded deterministic slice now demonstrates:

1. supervised local-first portfolio progression across more than one registered project
2. project-scoped isolation for state, branches, workspaces, and carry-forward memory
3. dependency-aware next-task selection with conservative stop posture
4. compatibility-preserving hosted-authority truth and merge-eligibility truth
5. green-gated proof-claim discipline
6. targeted retry planning around missing deliverables and coupled compatibility surfaces
7. bounded subset preservation so targeted retries do not unnecessarily widen the changed-file set
8. explicit hosted-authority operational-readiness truth around the stable `ci-required` contract
9. a bounded autonomous one-task lane with scheduler bridging, explicit stop/requeue policy, supervised handoff, resume-state artifacts, and an operator proof bundle
10. a fresh supervised operational re-proof over the bounded one-task lane

## Scope honesty

Current proof scope remains explicitly limited to:

- deterministic local supervised operation
- bounded multi-project portfolio slices
- conservative stop-on-risk / stop-on-authority-unsatisfied posture
- compatibility-preserving self-heal and schema alias normalization contracts
- safe-lane autonomy only for one allowlisted safe task at a time under supervision
- operator-readable proof for the bounded one-task lane, not broad autonomy

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, arbitrary multi-task autonomous execution, or broad self-hosting control-plane autonomy.

## Next continuation target

The next tranche should shift from “more safe-lane plumbing” to **execution quality**:

1. define an external-style safe one-task evaluation corpus
2. make the bounded one-task lane behave like a real dev / test / repair / controller loop
3. improve targeted self-heal quality on ordinary external-safe failures
4. measure pass rate and failure-class distribution
5. re-prove the bounded one-task lane on that external-safe corpus
6. only then decide whether bounded two-task trials are justified

## Task 149 checkpoint

Task 149 establishes the canonical external-safe evaluation manifest that later execution-quality tasks will use as the proving ground for one-task autonomous performance. The manifest carries:

- explicit archetype labels for ordinary external-style work
- allowed execution-lane truth per corpus item
- expected validation-profile truth per corpus item
- exact deliverable markdown text that later one-task runs can execute consistently
