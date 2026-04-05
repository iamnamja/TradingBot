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
- **083–088 harden the controller contract, retry/self-heal truth, merge/resume truth, controller repair context, strict mode, and further `run_task.py` decomposition**
- **089 synchronizes the hardened short-manifest proof surface and docs**
- Product is reusable and increasingly standardized, but **not extracted** as a standalone repo/package.

## What the product can honestly claim today

The repo now has:

- deterministic task-list manifest parsing and queue construction
- persisted machine-readable batch state and checkpointing
- canonical sequential batch executor/controller loop
- final acceptance review before advance
- accepted-task PR/check/merge/reset posture
- explicit resume-after-merge and manual-resolution semantics
- one canonical controller contract across controller-facing modules
- explicit non-reexecuting retry/self-heal semantics for the proof slice
- first-class merge/reset posture truth persisted consistently
- controller-core semantic repair digest/context
- controller strict mode with focused proof tests before full validation
- deterministic local proof of a hardened short ordinary-manifest autonomous progression slice

That proof is intentionally narrow and currently demonstrates:

1. task execution
2. authoritative validation
3. final acceptance review
4. retryable self-heal without raw re-execution
5. accepted-task PR/check/merge/reset gate
6. truthful stop on failed merge/check/reset posture
7. truthful resume-after-merge skip semantics based on persisted checkpoint truth
8. no premature proof-complete claims for docs/README before focused controller proof tests are green

It does **not** honestly claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across any task shape
- broad autonomy for protected/controller/meta task families

## Hardened proof boundary

The hardened autonomy proof remains intentionally bounded to:

- short ordinary/non-protected manifests
- deterministic local test harnesses and stubs
- conservative stop on non-autonomous signals
- controller-core tasks running under strict-mode proof gates

It is not a claim of broad arbitrary-task scheduler autonomy, and it does not override protected/controller lane controls.

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
  - retryable self-heal (budgeted, without raw re-execution for the same attempt)
  - per-task outcome persistence
  - conservative advance-or-stop decision
- Accepted-task PR/check/merge/reset posture
- Explicit resume semantics after merge and after manual resolution
- Controller strict-mode proof gates for controller-core tasks

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

## Merge posture truth and resume contract

- merge-posture outcomes (`failed_merge`, `failed_checks`, `failed_reset`) are first-class terminal controller truth
- persisted checkpoint truth carries canonical merge/reset evidence: `accepted_task_pr_flow_completed`, `required_checks_passed`, `merged_to_main`, `clean_main_reset_completed`
- `resume_after_merge` only skips prior tasks when persisted checkpoint truth proves accepted + completed + checks passed + merged to main + clean main reset
- `resume_after_manual_resolution` requires explicit operator intent and canonical resume metadata before execution may continue

## Remaining boundary conditions

The product still needs future work before any broader autonomy claim would be honest, especially around:

- broader protected/controller/meta task-family coverage
- larger manifests and more diverse task shapes
- wider unattended operational environments beyond the deterministic local proof harness
