# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 137–142 are complete in bounded supervised scope plus a narrow one-task autonomous lane:** the repo now converges around the stable `ci-required` contract surface, allowlists ordinary one-task autonomy conservatively, provides a dedicated bounded single-task runner, persists deterministic run ledgers and canary metrics, emits explicit supervised handoff artifacts for out-of-lane work, and re-proves that only one allowlisted safe task at a time is autonomous.

The current bounded deterministic slice now demonstrates:

1. supervised local-first portfolio progression across more than one registered project
2. project-scoped isolation for state, branches, workspaces, and carry-forward memory
3. dependency-aware next-task selection with conservative stop posture
4. compatibility-preserving hosted-authority truth and merge-eligibility truth
5. green-gated proof-claim discipline
6. targeted retry planning around missing deliverables and coupled compatibility surfaces
7. bounded subset preservation so targeted retries do not unnecessarily widen the changed-file set
8. explicit hosted-authority operational-readiness truth, including conservative interpretation of missing or weak required-check evidence
9. a fresh supervised resilience re-proof over the recent failure corpus
10. a bounded one-task autonomous lane with deterministic ledger, canary reporting, and supervised handoff artifacts

## Scope honesty

Current proof scope remains explicitly limited to:

- deterministic local supervised operation
- bounded multi-project portfolio slices
- conservative stop-on-risk / stop-on-authority-unsatisfied posture
- compatibility-preserving self-heal and schema alias normalization contracts
- extraction preparation posture rather than completed standalone extraction
- at most one allowlisted safe task at a time under supervision
- self-hosting control-plane work remains escalation-first unless separately proven safe

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, or broad multi-language portability.

## Next continuation target

The next tranche should focus on making the safe lane operationally trustworthy end to end:

1. tolerate the initial GitHub reporting race with a settle window and dual-surface hosted-authority probe
2. add a real-PR smoke proof for the stable `ci-required` contract
3. bridge the scheduler directly to the bounded single-task runner when exactly one safe task is ready
4. add conservative stop/requeue policy for mixed safe and supervised-only queues
5. make bounded one-task resume/re-entry idempotent and artifact-safe
6. produce an operator-readable proof bundle for the live canary lane
