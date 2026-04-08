# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 124–139 are complete in bounded supervised scope plus a narrow safe-lane canary:** the repo now freezes public/tested compatibility surfaces, normalizes schema aliases and canonical stop vocabulary, targets assertion-shaped failures toward coupled compatibility surfaces, gates proof tasks on exact deliverable contracts, distinguishes empty/underfilled/markerless/malformed bundle failures, compiles targeted retry prompts around missing deliverables, preserves the last-known-good subset while rolling back only the failing subset during retries, keeps hosted-authority operational convergence truth explicit, adds a safe task-family autonomy allowlist, and introduces a dedicated autonomous single-task runner with a persisted run ledger.

The current bounded deterministic slice now demonstrates:

1. supervised local-first portfolio progression across more than one registered project
2. project-scoped isolation for state, branches, workspaces, and carry-forward memory
3. dependency-aware next-task selection with conservative stop posture
4. compatibility-preserving hosted-authority truth and merge-eligibility truth
5. green-gated proof-claim discipline
6. targeted retry planning around missing deliverables and coupled compatibility surfaces
7. bounded subset preservation so targeted retries do not unnecessarily widen the changed-file set
8. explicit hosted-authority operational-readiness truth, including blocking `no checks reported` posture
9. a fresh supervised resilience re-proof over the recent failure corpus
10. a bounded autonomous single-task canary runner with persisted ledger artifacts
11. durable canary metrics and recovery reporting artifacts so single-task convergence can be measured without claiming a broad dashboard or unattended scheduler

## Scope honesty

Current proof scope remains explicitly limited to:

- deterministic local supervised operation
- bounded multi-project portfolio slices
- conservative stop-on-risk / stop-on-authority-unsatisfied posture
- compatibility-preserving self-heal and schema alias normalization contracts
- extraction preparation posture rather than completed standalone extraction
- safe-lane autonomy only after real operational enforcement is converged

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, or broad multi-language portability.

## Next continuation target

The next tranche should focus on moving from resilience hardening toward a **safe autonomous single-task lane**:

1. operationally converge hosted required-check / branch-protection truth with the real GitHub setup
2. introduce an allowlisted task-family admission lane for autonomous single-task runs
3. extend the single-task runner ledger into durable canary metrics and recovery reporting artifacts
4. produce explicit escalation artifacts for self-hosting control-plane tasks that still require supervised/manual handling
5. re-prove autonomous single-task execution only after the above lane is green
