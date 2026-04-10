# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 124–154 are complete in bounded supervised scope:** the repo now freezes public/tested compatibility surfaces, normalizes schema aliases and canonical stop vocabulary, targets assertion-shaped failures toward coupled compatibility surfaces, gates proof tasks on exact deliverable contracts, distinguishes empty/underfilled/markerless/malformed bundle failures, compiles targeted retry prompts around missing deliverables, preserves the last-known-good subset while rolling back only the failing subset during retries, keeps hosted-authority operational convergence truth explicit, verifies real GitHub required-check enforcement convergence around the stable `ci-required` context, establishes a safe task-family autonomy allowlist, adds a bounded autonomous single-task runner with ledger/reporting/handoff/resume semantics, routes the scheduler through that runner when exactly one safe task is ready, applies conservative stop/requeue policy for mixed queues, packages the lane into an operator-readable live canary proof bundle, defines the canonical external-safe evaluation manifest, records a deterministic one-task developer / verifier / repair / controller loop, classifies ordinary external-safe failures into narrower self-heal lanes, emits scoreboarding and failure-digest artifacts, re-proves the current external-safe corpus reliability band, and now defines the explicit go / no-go gate for any bounded two-task widening.

The current bounded deterministic slice now demonstrates:

1. supervised local-first portfolio progression across more than one registered project
2. project-scoped isolation for state, branches, workspaces, and carry-forward memory
3. dependency-aware next-task selection with conservative stop posture
4. compatibility-preserving hosted-authority truth and merge-eligibility truth
5. green-gated proof-claim discipline
6. targeted retry planning around missing deliverables and coupled compatibility surfaces
7. bounded subset preservation so targeted retries do not unnecessarily widen the changed-file set
8. explicit hosted-authority operational-readiness truth around the stable `ci-required` contract
9. a bounded autonomous one-task lane with scheduler bridging, explicit stop/requeue policy, supervised handoff, resume-state artifacts, operator proof bundle, and role-separated execution record
10. measured one-task execution-quality artifacts: canary metrics, recovery report, failure taxonomy, and failure digest
11. an explicit readiness gate that decides whether bounded two-task trials are earned by measured one-task results

## Scope honesty

Current proof scope remains explicitly limited to:

- deterministic local supervised operation
- bounded multi-project portfolio slices
- conservative stop-on-risk / stop-on-authority-unsatisfied posture
- compatibility-preserving self-heal and schema alias normalization contracts
- safe-lane autonomy only for one allowlisted safe task at a time under supervision
- operator-readable proof for the bounded one-task lane, not broad autonomy
- a phase gate for possible bounded two-task trials, not an actual widened two-task rollout

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, arbitrary multi-task autonomous execution, or broad self-hosting control-plane autonomy.

## Task 154 checkpoint

Task 154 adds the explicit widening gate for bounded two-task trials. The gate is intentionally concrete and conservative:

- at least **6** evaluated external-safe one-task runs
- at least **0.75** one-task completion rate
- at most **0.25** escalation rate
- at most **0.10** hosted-authority block rate
- at most **0.34** self-healed completion share
- direct completions must exceed self-healed completions

The current truthful posture remains **no-go** for bounded two-task widening. The latest external-safe re-proof band is still approximately **4 of 6** completed, with **2 of 4** completions requiring bounded self-heal, so the lane has improved materially but has not yet earned the right to widen.

## Next continuation target

The next continuation target is still **one-task execution quality**:

1. raise external-safe one-task completion rate above the widening threshold
2. reduce escalation-required outcomes
3. reduce hosted-authority blocking noise where possible without faking authority truth
4. make direct completions clearly outnumber self-healed completions
5. keep two-task widening closed until those measured criteria are satisfied
