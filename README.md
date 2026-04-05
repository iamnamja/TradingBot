# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The reliability/autonomy tranche and the first backlog-execution continuation are now complete through **Task 075**.

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

The agent runner now supports a conservative batch mode in addition to single-task mode.

- Input: a task-list manifest (ordered task paths)
- Behavior: sequential execution, intentionally conservative
- Stop posture: may stop at first blocking/manual/failure outcome
- Goal: reviewable progression over broad autonomy

Single-task behavior remains available and unchanged for normal `agents/run_task.py <task.md>` usage.

## What batch mode can honestly claim today

Today the repo has:

- a first conservative batch runner CLI
- machine-readable and human-readable batch summaries
- a first narrow end-to-end proof that short sequential backlog execution works under deterministic local tests

It does **not** yet honestly claim a broad unattended arbitrary-task scheduler. The 076–082 tranche is about closing that gap for short ordinary-task manifests.

## Documentation entry points

- `docs/README.md` — docs index and reading order
- `docs/TRADINGBOT_PROJECT_STATE.md` — authoritative current state and tranche boundaries
- `docs/ORCHESTRATOR_ROADMAP_069_075.md` — historical roadmap context for the first backlog-execution slice
- `docs/ORCHESTRATOR_ROADMAP_076_082.md` — next autonomy-and-controller-thinning tranche
- `tasks/README.md` — canonical numbered task map

## Development

- Lint: `ruff check .`
- Tests: `pytest -q`

## Documentation placement

`README.md` is the canonical root-level entrypoint for the repo. Orchestrator and TradingBot narrative documents, product specs, controls/policies docs, and relationship documents should live under `docs/` rather than being duplicated at repo root.
