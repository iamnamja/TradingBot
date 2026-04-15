# Task 204 — orchestrator controller route trace and resume reconstruction for canary runs

## Why

The project goal is not just to run a few adjacent tasks. It is for the orchestrator to sit in the middle, decide which role should act next, and preserve that truth across interruptions. The next widening slice therefore needs a durable controller-route trace for chained canary work.

## Scope

Persist controller route decisions and resume reconstruction truth for supervised three-step canary runs.

## Runtime seams to reuse

- Reuse controller / builder / verifier contract vocabulary already present in the repo.
- Reuse role artifact envelope and handoff truth where available.
- Reuse resume and checkpoint vocabulary from Task 198.
- Reuse the three-step canary ledger and benchmark artifacts from Tasks 201-203.

## Requirements

- Persist a durable controller route trace for chained canary runs that records at minimum:
  - current role,
  - proposed next role,
  - actual next role,
  - reason for the choice,
  - whether supervision influenced or overrode the route.
- Make interrupted canary runs reconstructable enough to recover pending-role truth.
- Keep the implementation additive and bounded to the canary path.
- Preserve compatibility with existing controller contract surfaces.

## Create or update these exact files

- `agents/lib/controller_route_trace.py`
- `tests/test_controller_route_trace.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/204_orchestrator_controller_route_trace_and_resume_reconstruction_for_canary_runs.md`

## Non-goals

- Do not redesign the full controller system for arbitrary manifests.
- Do not widen beyond supervised canary execution.
- Do not weaken existing controller compatibility surfaces.

## Acceptance criteria

- Tests prove controller route choices are persisted durably for canary runs.
- Tests prove resume reconstruction can recover pending-role truth after interruption.
- Tests prove supervision overrides remain explicit rather than hidden.
