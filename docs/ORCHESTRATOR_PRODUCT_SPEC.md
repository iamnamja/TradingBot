# Orchestrator Product Spec (In-Repo Productizing Engine)

## Product intent

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, and seam-aware testability.

## Current product stage

- **Post-048 baseline achieved** (042–048 complete)
- **049–052 complete on `main`**
- **Reliability/autonomy continuation complete through 067** (including 065a and 067a)
- **Protected/controller stabilization complete through 069** (including 068, 068a, 068b, and 068c)
- **070 adds task-list manifest and queue groundwork for backlog execution**
- **070b clarifies runtime-artifact lifecycle controls with explicit retention mode**
- **071 adds persisted batch-state and deterministic resume groundwork for queue execution**
- **074 adds first conservative batch-runner CLI mode with summary artifacts**
- **078 adds a dedicated canonical batch executor/controller loop for sequential per-task execution + acceptance + conservative stop**
- **080 adds explicit resume semantics for post-merge continuation and manual-resolution recovery**
- Product is reusable and increasingly standardized, but **not yet extracted** as a standalone repo/package.

## Users and use cases

- Engineering operators running governed task workflows
- Projects requiring deterministic, policy-constrained automation
- Multi-project environments where adapter-driven portability matters
- Repositories that need stable test seams and guarded integrated coverage before extraction

## Core capabilities

- Structured task ingestion and contract parsing
- Safety harness with protected-file policies and semantic preflight checks
- Controlled execution shell and command routing
- Review/compliance/approval gates
- Backlog state tracking and recovery
- Audit logging and failure journaling
- Optional dry-run/simulation and safe parallelism
- Multi-project adapter support
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
- Explicit resume controller posture:
  - resume same task (explicit)
  - resume next task (explicit)
  - skip accepted+merged tasks on resume-after-merge
  - resume previously manual/blocked task only with explicit operator intent

## Canonical sequential batch controller loop (078/080)

The batch executor/controller loop is the canonical manifest execution path for sequential task processing.

Per queued task, the controller performs:

1. transition task to running
2. execute task attempt
3. run authoritative validation
4. run final acceptance review
5. if acceptance is retryable and retry budget remains, run self-heal + retry
6. persist terminal task outcome + checkpoint/state updates
7. continue to next task only when terminal decision is safe (`continue`)

Conservative stop posture is preserved:

- terminal `manual_patch` stops the batch
- terminal `blocked` stops the batch
- non-accepted terminal failures stop the batch unless explicit continue conditions are met

Resume posture is now explicit and persisted:

- **resume-after-merge** may skip prior tasks only when checkpoint evidence is `accepted` + terminal `completed`
- **manual/blocked recovery** requires explicit resume mode and target; never skipped implicitly
- resume gate/reason/target are persisted for deterministic replay and operator inspection

## Per-task persisted outcome requirements

Persisted state/checkpoints explicitly capture at least:

- `task_path`
- terminal status
- final acceptance decision
- retry count used
- whether next task may proceed
- post-task decision (`continue|stop|manual_patch|blocked`)

Resume metadata persisted in batch state:

- `resume_reason`
- `resume_target_task_path`
- `resume_gate`

This is explicit by design; implicit in-memory controller state is not the source of truth.

## Documentation and implementation intent

The dedicated batch executor/controller loop is intentionally:

- sequential
- deterministic
- conservative by default
- acceptance-gated before advance
- safe for resume/state replay
- explicit about when skip/resume is allowed

No concurrent scheduling is introduced in this tranche.

## Runtime artifact lifecycle policy

Known-safe runtime scratch artifacts include files such as:

- `last_output.txt`
- `_last_agent_model_output.txt`
- `_last_agent_file_bundle.txt`

Default posture on successful push flow:

- remove these known-safe scratch artifacts from disk as part of quarantine cleanup
- unstage them from index before staging (`git rm --cached --ignore-unmatch`)
- prevent accidental commit drift from temporary runtime files

Explicit retention mode:

- operators may opt in to retain known-safe scratch artifacts on disk for forensic/debug review
- retention is narrow and explicit (flag/env driven), never implicit default behavior
- even when retained, known-safe artifacts remain unstaged by default controller behavior

Unknown runtime artifacts:

- are never treated as known-safe retained scratch
- continue to trigger protective blocking behavior until resolved
- are messaged as blocked unknowns, distinct from known-safe retention/removal

## Success criteria for extraction readiness

- Stable public interfaces with tested compatibility
- Stable seam registry for orchestrator integration tests
- Preflight can catch common seam/task-shape mistakes early
- Demonstrated portability beyond the primary project
- Manifest/queue semantics validated under test
- Batch state + deterministic resume validated under test
- Canonical batch executor/controller loop with explicit per-task persisted outcomes and acceptance-gated advancement
- Resume-after-merge and explicit manual-resolution resume semantics validated under test
- Documentation/state surfaces synchronized and unambiguous
