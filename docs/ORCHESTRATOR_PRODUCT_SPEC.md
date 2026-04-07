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
- **090–099 synchronize multi-agent contract + portability proof + extraction-prep boundary posture**
- **100–106 harden resilience and add external bootstrap recovery proof**
- **107 adds a supervised mixed-manifest local-first re-proof over multiple task families**
- Product is reusable and increasingly standardized, but **not extracted** as a standalone repo/package.

## What the product can honestly claim today

The repo now has deterministic proof for:

- role separation across `controller`, `builder`, and `verifier`
- sequential multi-agent loop with controller-owned final decision authority
- dependency-aware short-manifest planning/routing
- explicit verification-authority posture in the decision truth
- second-project Python portability proof for a simple generic Python workspace
- explicit monorepo consumer-boundary snapshot as extraction preparation, not completed extraction
- explicit external bootstrap blocked-then-recovered truth for a simple external Python workspace
- supervised mixed-manifest progression and conservative stop when authority is unsatisfied

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduling across arbitrary task families
- broad arbitrary multi-language portability
- full standalone extraction is complete

## Hardened proof boundary

The synchronized post-107 proof remains intentionally limited to deterministic local tests and demonstrates at most:

1. controller/builder/verifier role separation
2. dependency-aware short-manifest progression
3. explicit verification-authority truth
4. Python-only second-project portability
5. truthful external bootstrap blocked-then-recovered recovery
6. supervised mixed-manifest progression across proof/docs + bootstrap + consumer-facing task shapes
7. conservative stop on unsatisfied authority
8. extraction-prep consumer boundary posture without over-claiming full extraction

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
- Canonical sequential batch executor loop with conservative advance/stop behavior
- Accepted-task PR/check/merge/reset posture with truthful failure stop states
- Explicit resume semantics after merge and after manual resolution
- Controller strict-mode proof gates for controller-core tasks
- Python-first second-project workspace adapter selection and bootstrap truth tracking
- Sequential multi-agent builder/verifier/controller proof loop over short dependency-aware manifests
- Targeted repair planner that prefers the smallest plausible compatibility/docs adapter for bounded failures
- Supervised local-first mixed-manifest re-proof lane with bounded max-task progression and authority stop guardrails

## Boundary and claim discipline

Public claims in docs/README must remain narrower than or equal to deterministic proof tests. This remains in force for the multi-agent portability tranche.


## Result-shape and manifest-schema normalization

The proof-facing portability surface now normalizes manifest entries through one canonical adapter and normalizes loop results through one bounded compatibility adapter. This keeps `path` vs `task_path` drift and proof-facing result-field drift from breaking otherwise valid tasks.


## External workspace bootstrap recovery proof (106)

The current bounded proof now also covers a simple external Python workspace that first enters a `blocked` bootstrap state and then recovers truthfully into `succeeded`, with resume-safe recovery semantics kept explicit and deterministic.


## Supervised mixed-manifest autonomy re-proof (107)

The current bounded proof also covers a short supervised mixed manifest that spans multiple task families (proof/docs, bootstrap, consumer-facing) and confirms:

- planner/routing/bootstrap/verification/controller surfaces are used together in one deterministic slice
- the loop remains local-first and bounded by explicit `max_tasks`
- when verification authority is unsatisfied, controller decision is conservative `stop`
