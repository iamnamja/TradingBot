# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 124–165 are complete in bounded supervised scope:** the repo now freezes public/tested compatibility surfaces, gates proof tasks on exact deliverable contracts, distinguishes malformed and empty bundle failures, preserves last-known-good subsets during retries, maintains bounded autonomous one-task execution, adds benchmark scorecard integration, improves authority-gate evidence handling, hardens deliverable contracts and completion prompts, normalizes runtime artifact hygiene, and completes a second one-task reliability minipack re-proof.

The current bounded slice now demonstrates:

1. supervised local-first portfolio progression across more than one registered project
2. project-scoped isolation for state, branches, workspaces, and carry-forward memory
3. dependency-aware next-task selection with conservative stop posture
4. compatibility-preserving hosted-authority truth and merge-eligibility truth
5. green-gated proof-claim discipline
6. targeted retry planning around missing deliverables and coupled compatibility surfaces
7. bounded subset preservation so targeted retries do not unnecessarily widen the changed-file set
8. a bounded autonomous one-task lane with scheduler bridging, explicit stop or requeue policy, supervised handoff, resume-state artifacts, and operator proof bundles
9. strict scorecard and re-proof artifacts that still keep the project in one-task reliability mode rather than broad autonomy mode

## Scope honesty

Current proof scope remains explicitly limited to:

- deterministic local supervised operation
- bounded multi-project portfolio slices
- conservative stop-on-risk / stop-on-authority-unsatisfied posture
- compatibility-preserving self-heal and schema alias normalization contracts
- safe-lane autonomy only for one allowlisted safe task at a time under supervision
- operator-readable proof for the bounded one-task lane, not broad autonomy

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, arbitrary multi-task autonomous execution, or broad self-hosting control-plane autonomy.

## Current continuation target

The project should remain in **one-task reliability mode**.

The next tranche should focus on:

1. a strict no-manual-intervention scorecard
2. better authority corroboration and run truth
3. elimination of the dominant remaining one-task failure family
4. a formal promotion re-proof for the one-task lane
5. only then, a gated decision on whether eligible one-task work should become the default orchestrator path and whether a bounded two-task pilot is justified

## Reliability sprint checkpoint

Tasks 157–165 improved the one-task lane materially, but the second minipack re-proof still supports another reliability sprint instead of immediate widening.
