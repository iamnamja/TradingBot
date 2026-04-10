# Task 165 — orchestrator one-task reliability minipack re-proof

## Goal
Run a small fixed pack of benchmark-eligible one-task jobs through the orchestrator and produce a fresh reliability readout after Tasks 161–164 land.

## Why
The project now needs measured proof that one-task execution is improving in real life, not just more feature slices.

## Requirements
- Define a fixed minipack of 3–5 benchmark-eligible one-task tasks.
- Run them through the orchestrator with the proof-mode settings.
- Count any human mid-run code edit as a failed autonomous run.
- Produce a short re-proof summary showing direct completion, repaired completion, transport failure, and blocked/escalated counts.

## Acceptance
- The minipack and run settings are documented.
- Re-proof artifacts are machine-readable.
- Docs/state are updated with the resulting reliability posture.
