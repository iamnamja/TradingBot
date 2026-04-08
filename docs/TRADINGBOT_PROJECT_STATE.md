# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 124–138 are complete in bounded supervised scope:** the repo now freezes public/tested compatibility surfaces, normalizes schema aliases and canonical stop vocabulary, targets assertion-shaped failures toward coupled compatibility surfaces, gates proof tasks on exact deliverable contracts, distinguishes empty/underfilled/markerless/malformed bundle failures, compiles targeted retry prompts around missing deliverables, preserves the last-known-good subset while rolling back only the failing subset during retries, keeps hosted-authority operational convergence truth explicit, re-proves the bounded supervised resilience corpus over the concrete failure classes from Tasks 130–135, and now verifies real GitHub required-check enforcement convergence around the stable `ci-required` context instead of relying only on modeled local contract truth, and now adds an explicit safe task-family autonomy allowlist that only admits narrow ordinary single-task work while escalating self-hosting control-plane edits by default.

The current bounded deterministic slice now demonstrates:

1. supervised local-first portfolio progression across more than one registered project
2. project-scoped isolation for state, branches, workspaces, and carry-forward memory
3. dependency-aware next-task selection with conservative stop posture
4. compatibility-preserving hosted-authority truth and merge-eligibility truth
5. green-gated proof-claim discipline
6. targeted retry planning around missing deliverables and coupled compatibility surfaces
7. bounded subset preservation so targeted retries do not unnecessarily widen the changed-file set
8. explicit hosted-authority operational-readiness truth, including blocking `no checks reported` posture
9. real GitHub required-check enforcement convergence truth for the configured `ci-required` contract on the repo base branch
10. a fresh supervised resilience re-proof over the recent failure corpus

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

1. add a dedicated single-task runner, run ledger, and canary metrics on top of the new allowlisted admission lane
2. produce explicit escalation artifacts for self-hosting control-plane tasks that still require supervised/manual handling
3. re-prove autonomous single-task execution only after the above lane is green
