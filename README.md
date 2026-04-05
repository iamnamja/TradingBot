# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The reliability/autonomy continuation, backlog-execution hardening, controller-contract hardening, and proof synchronization tranche are now complete through **Task 089**.

The proof-backed controller continuation covered by the current repo state is:

- **076–089** — autonomous backlog progression, controller hardening, and proof synchronization
  - final acceptance reviewer/report
  - targeted self-heal for acceptance failures
  - explicit batch executor/controller loop
  - accepted-task PR/check/merge/reset flow
  - resume-after-merge and manual-resolution behavior
  - canonical controller contract
  - non-reexecuting retry/self-heal semantics
  - merge-posture truth persistence and resume contract
  - semantic controller repair digest/context
  - controller strict mode and patch-quality gate
  - further `agents/run_task.py` decomposition
  - hardened autonomous short-manifest proof

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for the authoritative status narrative.

## Current batch posture

The agent runner supports a conservative batch mode in addition to single-task mode.

- Input: a task-list manifest (ordered task paths)
- Behavior: sequential execution, authoritative validation, final acceptance review, deterministic repair-without-raw-reexecution, and per-task persisted truth
- Stop posture: stops honestly on blocking/manual/merge-posture failures
- Goal: truthful, reviewable progression over a short ordinary manifest proof slice

Single-task behavior remains available and unchanged for normal `agents/run_task.py <task.md>` usage.

## What the repo can honestly claim today

Today the repo has:

- a conservative batch runner CLI
- machine-readable and human-readable batch summaries
- one canonical controller contract across controller-facing modules
- non-reexecuting retry/self-heal semantics with separate raw-execution vs repair proof in tests
- first-class merge-posture truth persistence and resume gates
- controller-core semantic repair digest/context
- controller strict mode with focused controller proof tests before full validation
- deterministic local proof of a hardened short ordinary-manifest autonomous progression slice

That proof currently covers:

1. task execution
2. authoritative validation
3. final acceptance review
4. retryable self-heal without raw re-execution
5. accepted-task PR/check/merge/reset gate
6. truthful stop on failed merge/check/reset posture
7. truthful resume-after-merge skip behavior based on persisted truth
8. proof-claim deferral for docs/README until focused controller proof tests are green

It does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduler autonomy across any task shape
- hidden always-on autonomy for protected/controller/meta tasks

## Next planned tranche

The next planned tranche is **090–099** — multi-agent portability and productization.

Planned areas:

- canonical builder/verifier/controller role contract and handoff truth
- explicit sequential builder/verifier/controller loop
- CI-required checks as first-class verification authority
- repair-strategy routing rather than one generic remediation lane
- reusable project/workspace bootstrap and validation contracts
- dependency-aware manifests and task-family routing
- a second-project Python portability proof
- a clearer standalone product boundary while remaining in the monorepo for this tranche

## Accepted-task autonomous PR/merge posture (optional)

For tasks that have passed final acceptance review, the orchestrator can optionally run:

1. PR creation
2. required-check watch
3. merge after successful checks
4. clean reset to `main` (switch/fetch/reset/clean)
5. only then unlock next-task progression

Conservative limits:

- no auto-merge for tasks that are not accepted
- PR/CI/merge/reset failures stop honestly and persist non-proceed state
- next task cannot proceed unless clean-main reset succeeds
- operator-controlled mode remains available (autonomous merge is not hidden always-on)

## Scope boundary for the autonomy proof

The current proof is intentionally narrow:

- short ordinary/non-protected manifests
- deterministic local tests and stubs
- conservative stop-on-risk posture
- controller-core discipline enforced by strict-mode proof gates

It remains an intentionally bounded proof slice rather than a claim of broad scheduler autonomy.

## Documentation entry points

- `docs/README.md` — docs index and reading order
- `docs/TRADINGBOT_PROJECT_STATE.md` — authoritative current state and tranche boundaries
- `docs/ORCHESTRATOR_ROADMAP_076_082.md` — pre-hardening autonomous backlog proof tranche
- `docs/ORCHESTRATOR_ROADMAP_083_089.md` — controller-contract hardening tranche through the hardened short-manifest proof
- `docs/ORCHESTRATOR_ROADMAP_090_099.md` — multi-agent portability and productization tranche after Task 089
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md` — control gates and policy posture
- `docs/orchestrator_extraction_plan.md` — current `agents/run_task.py` decomposition map
- `tasks/README.md` — canonical numbered task map

## Development

- Lint: `ruff check .`
- Tests: `pytest -q`

## Documentation placement

`README.md` is the canonical root-level entrypoint for the repo. Orchestrator and TradingBot narrative documents, product specs, controls/policies docs, and relationship documents should live under `docs/` rather than being duplicated at repo root.
