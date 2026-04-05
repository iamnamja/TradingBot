# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The reliability/autonomy tranche and backlog-execution continuation are complete through **Task 082**.

The active sequence covered by the current proof is:

- **076–082** — autonomous backlog progression and controller-thinning continuation
  - final acceptance reviewer/report
  - targeted self-heal for acceptance failures
  - explicit batch executor/controller loop
  - accepted-task PR/check/merge/reset flow
  - resume-after-merge and manual-resolution behavior
  - further `agents/run_task.py` decomposition
  - autonomous backlog-runner proof for a short ordinary-task manifest

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for status narrative.

## Current batch posture

The agent runner supports a conservative batch mode in addition to single-task mode.

- Input: a task-list manifest (ordered task paths)
- Behavior: sequential execution, acceptance-gated progression, deterministic retry/self-heal slice
- Stop posture: stops honestly on blocking/manual/merge-posture failures
- Goal: truthful, reviewable progression over a short ordinary manifest proof slice

Single-task behavior remains available and unchanged for normal `agents/run_task.py <task.md>` usage.

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

## Autonomous backlog runner proof (Task 082)

The repository now includes deterministic E2E-oriented tests proving that a short ordinary manifest can:

1. run a task
2. pass authoritative validation and final acceptance
3. merge/reset cleanly
4. continue to the next task

It also proves:

- retryable acceptance failure can self-heal and then continue
- `manual_patch`, `blocked`, and failed merge posture stop conservatively
- persisted state/outcomes reflect run truthfully

## What batch mode can honestly claim today

Today the repo has:

- a conservative batch runner CLI
- machine-readable and human-readable batch summaries
- deterministic local proofs for short ordinary-manifest autonomous progression

It does **not** claim:

- arbitrary protected/controller task-list autonomy
- broad unattended production scheduler autonomy across any task shape

## Documentation entry points

- `docs/README.md` — docs index and reading order
- `docs/TRADINGBOT_PROJECT_STATE.md` — authoritative current state and tranche boundaries
- `docs/ORCHESTRATOR_ROADMAP_069_075.md` — historical roadmap context for the first backlog-execution slice
- `docs/ORCHESTRATOR_ROADMAP_076_082.md` — next autonomy-and-controller-thinning tranche
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md` — control gates and policy posture
- `tasks/README.md` — canonical numbered task map

## Development

- Lint: `ruff check .`
- Tests: `pytest -q`

## Documentation placement

`README.md` is the canonical root-level entrypoint for the repo. Orchestrator and TradingBot narrative documents, product specs, controls/policies docs, and relationship documents should live under `docs/` rather than being duplicated at repo root.