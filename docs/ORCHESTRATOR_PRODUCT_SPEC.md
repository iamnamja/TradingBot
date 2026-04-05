# Orchestrator Product Spec (In-Repo Productizing Engine)

## Product intent

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, and seam-aware testability.

## Current product stage

- **Post-048 baseline achieved** (042–048 complete)
- **049–052 complete on `main`**
- **Reliability/autonomy continuation complete through 067** (including 065a and 067a)
- **Protected/controller stabilization complete through 069** (including 068, 068a, 068b, and 068c)
- **070 adds task-list manifest and queue groundwork for backlog execution**
- **071 adds persisted batch-state and deterministic resume groundwork for queue execution**
- **074 adds first conservative batch-runner CLI mode with summary artifacts**
- **076–081 add final acceptance review, targeted self-heal, batch executor loop, accepted-task PR/merge/reset gate, resume semantics, and further controller decomposition**
- **082 adds the first narrow autonomous backlog-runner proof for a short ordinary manifest**
- Product is reusable and increasingly standardized, but **not yet extracted** as a standalone repo/package.

## What the product can honestly claim today

The repo now has:

- deterministic task-list manifest parsing and queue construction
- persisted machine-readable batch state and checkpointing
- canonical sequential batch executor/controller loop
- final acceptance review before advance
- accepted-task PR/check/merge/reset posture
- explicit resume-after-merge and manual-resolution semantics
- deterministic local proof of a short ordinary-manifest autonomous progression slice

It does **not** yet honestly claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across any task shape

## Current product gaps after 082

Task 082 exposed the next set of hardening priorities:

- controller modules still need one canonical contract for decisions and truth fields
- retryable self-heal must be explicitly non-reexecuting everywhere with separate execution-vs-repair truth
- merge/reset posture truth must be first-class and persisted consistently
- controller-task failures need a semantic repair digest, not just raw logs
- controller-core tasks need stricter patch-quality gates and proof-claim deferral

These are the basis of the next tranche.

## Next planned tranche (083–089)

- **083** — controller contract canonicalization
- **084** — non-reexecuting retryable self-heal channel
- **085** — merge-posture truth persistence and resume contract
- **086** — semantic failure digest and controller repair context
- **087** — controller-task strict mode and patch-quality gate
- **088** — controller decomposition fourth extraction
- **089** — hardened autonomous short-manifest proof

## Core capabilities

- Structured task ingestion and contract parsing
- Safety harness with protected-file policies and semantic preflight checks
- Controlled execution shell and command routing
- Review/compliance/approval gates
- Backlog state tracking and recovery
- Audit logging and failure journaling
- Stable seam registry for orchestrator integration testing
- Deterministic task-list manifest parsing and queue construction
- Persisted machine-readable batch state for task-list execution and deterministic resume
- Canonical sequential batch executor loop:
  - execute task
  - authoritative validation
  - final acceptance review
  - retryable self-heal (budgeted)
  - per-task outcome persistence
  - conservative advance-or-stop decision
- Accepted-task PR/check/merge/reset posture
- Explicit resume semantics after merge and after manual resolution

## Canonical sequential batch controller loop

The batch executor/controller loop is the canonical manifest execution path for sequential task processing.

Per queued task, the controller performs:

1. transition task to running
2. execute task attempt
3. run authoritative validation
4. run final acceptance review
5. if acceptance is retryable and retry budget remains, run repair without raw re-execution, then re-validate and re-review
6. persist terminal task outcome plus checkpoint/state updates
7. continue to next task only when terminal decision is safe

Conservative stop posture is preserved:

- terminal `manual_patch` stops the batch
- terminal `blocked` stops the batch
- non-accepted terminal failures stop the batch unless explicit continue conditions are met
- accepted tasks with failed PR/CI/merge/reset posture stop with truthful failed decision

## Scope boundary for autonomy proof

The current autonomy proof is intentionally narrow:

- short ordinary/non-protected manifests
- deterministic local E2E test harness
- conservative stop on non-autonomous signals

It is **not** a claim of broad arbitrary-task scheduler autonomy, and it does not override protected/controller lane controls.

## Success criteria for the next tranche

The next tranche is successful when:

- controller-facing modules share one canonical contract module
- retryable self-heal is explicitly non-reexecuting and auditably persisted
- merge/reset posture truth is first-class and persisted consistently
- controller-task repair uses a semantic failure digest
- controller-core tasks run under stricter patch-quality and claim-deferral rules
- `agents/run_task.py` is materially thinner again
- a hardened short-manifest autonomous proof is green and honestly documented


## Post-082 controller hardening tranche (083–089)

- Task 084 makes retryable self-heal explicitly non-reexecuting: one raw execution attempt, bounded repair-only retries, then re-validation and final acceptance on the repaired result.
- Persisted controller truth must separately record `execution_attempt_count`, `repair_count`, and `accepted_after_repair` so repair loops are auditable without overstating raw task execution.
