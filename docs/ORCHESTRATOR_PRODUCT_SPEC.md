# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

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
- **090–098 establish multi-agent contracts, second-project Python portability proof coverage, and a clearer standalone package boundary**
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
- dependency-aware manifest planning with explicit blocked/deferred/skipped/rerun-required truth
- deterministic local second-project portability proof for a simple generic Python workspace using adapter-selected bootstrap and validation contracts
- deterministic local proof of sequential builder/verifier/controller role loop behavior with controller-owned continue/stop authority

That proof is intentionally narrow and currently demonstrates:

1. task execution
2. authoritative validation
3. final acceptance review
4. retryable self-heal without raw re-execution
5. accepted-task PR/check/merge/reset gate
6. truthful stop on failed merge/check/reset posture
7. truthful resume-after-merge skip semantics based on persisted checkpoint truth
8. no premature proof-complete claims for docs/README before focused controller proof tests are green
9. second-project Python-first adapter portability over a short dependency-aware manifest
10. truthful controller stop/continue outcomes sourced from verifier authority and explicit controller decision

It does **not** honestly claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across any task shape
- broad autonomy for protected/controller/meta task families
- broad arbitrary multi-language portability
- unattended end-to-end autonomy without verification authority constraints

## Next product target after 097

The next product step should evolve the orchestrator from a stronger single-controller task runner into a more explicit multi-agent project runner.

The intended first multi-agent architecture is intentionally conservative:

- **controller/orchestrator** decides what should happen next
- **builder/coder** proposes implementation patches or task outputs
- **verifier/tester** runs focused and full validation and summarizes evidence

This should remain sequential before any future concurrency or true parallel role scheduling is considered.




## Standalone package boundary and consumer bridge

The orchestrator now has a clearer standalone package boundary without claiming that full extraction is already complete.

The current consumer bridge is intentionally minimal and includes:

- workspace adapter/config
- validation commands
- acceptance evidence hooks
- protected path declarations
- optional consumer-specific policies

TradingBot remains a supported consumer, while generic Python is now an explicit second consumer shape.

## Project/workspace adapter v2 foundation

The portability surface now has a canonical workspace contract that can describe, at minimum:

- workspace root
- bootstrap/setup commands
- validation commands
- acceptance evidence commands
- protected paths
- artifact/output paths
- merge-policy constraints

The current portability scope remains Python-first. TradingBot is one supported consumer, not a hardcoded assumption.

## Hardened proof boundary

The hardened autonomy proof remains intentionally bounded to:

- short ordinary/non-protected manifests
- deterministic local test harnesses and stubs
- conservative stop on non-autonomous signals
- controller-core tasks running under strict-mode proof gates
- simple second-project Python workspace shapes through adapter contracts

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
- Python-first second-project workspace adapter selection and bootstrap truth tracking
- Sequential multi-agent builder/verifier/controller proof loop over short dependency-aware manifests

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

## Next capabilities the product still needs

Before any stronger “give it a whole project and let it build” claim would be honest, the product still needs:

- broader verification-authority profile coverage in real integrated environments
- stronger CI-backed verification authority in external repos beyond local proofs
- role-aware remediation routing depth for larger manifests
- broader task-family routing coverage
- a clearer standalone package boundary while the repo still remains a monorepo consumer setup

## Merge posture truth and resume contract

- merge-posture outcomes (`failed_merge`, `failed_checks`, `failed_reset`) are first-class terminal controller truth
- persisted checkpoint truth carries canonical merge/reset evidence: `accepted_task_pr_flow_completed`, `required_checks_passed`, `merged_to_main`, `clean_main_reset_completed`
- persisted controller state also records required-check discovery, missing/pending/timed-out/failed/pass truth, whether missing checks block merge, and whether the configured verification authority is satisfied
- `resume_after_merge` only skips prior tasks when persisted checkpoint truth proves accepted + completed + checks passed + merged to main + clean main reset
- `resume_after_manual_resolution` requires explicit operator intent and canonical resume metadata before execution may continue

## Remaining boundary conditions

The product still needs future work before any broader autonomy claim would be honest, especially around:

- broader protected/controller/meta task-family coverage
- larger manifests and more diverse task shapes
- wider unattended operational environments beyond the deterministic local proof harness
- portability beyond Python-first project shapes


## Dependency-aware manifest planner

The queue surface now needs to express dependency truth explicitly rather than treating every manifest as a fixed total order. The planner remains intentionally conservative:

- `depends_on` expresses prerequisites that must be completed before a task becomes ready
- `blocks` expresses tasks that are held back until the current task is completed
- `deferrable` allows the planner to choose a later ready task without violating dependency truth
- `skipped_by_policy` marks tasks that should remain visible but not scheduled
- `rerun_required` marks tasks whose prerequisite changes require a fresh pass

Planner decisions must be explicit and persisted. Resume should reconstruct the same planner truth instead of silently inventing a different order.
