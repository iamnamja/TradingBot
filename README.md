# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The reliability/autonomy tranche and the first backlog-execution continuation are now complete through **Task 079**.

The current next-stage active sequence is:

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
- Behavior: sequential execution, intentionally conservative
- Stop posture: may stop at first blocking/manual/failure outcome
- Goal: reviewable progression over broad autonomy

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

## What batch mode can honestly claim today

Today the repo has:

- a conservative batch runner CLI
- machine-readable and human-readable batch summaries
- deterministic local proofs for sequential backlog execution and accepted-task PR lifecycle gates under test

It does **not** claim broad unattended arbitrary-task scheduling. The 076–082 tranche is focused on closing that gap safely for short ordinary-task manifests.

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
