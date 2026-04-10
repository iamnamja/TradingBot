# Task 164 — orchestrator completion integrity gate

## Goal
Detect partial implementations that pass local checks but miss required integration surfaces, and fail those runs before they are treated as completed benchmark work.

## Why
The first autonomous Task 157 attempt produced a helper module and tests that went green, but the task still missed the benchmark/session integration points that made it actually complete.

## Requirements
- Extend completion evaluation to compare the produced change set against the task’s required integration surfaces.
- Fail a run when required benchmark/runtime/doc surfaces are missing even if ruff and pytest are green.
- Keep the gate narrow and task-contract driven.
- Avoid broad speculative heuristics.

## Acceptance
- A task that only adds a disconnected helper does not count as completed when integration surfaces are required.
- The gate emits a clear reason in the run artifacts.
- Tests cover both a fully integrated completion and a green-but-partial completion.
