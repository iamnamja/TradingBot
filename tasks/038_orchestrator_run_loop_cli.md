# Task 038 — Run Loop Workstream (Umbrella)

## Status

Do NOT run this umbrella task directly with the agent.

This workstream was split after Task 037 because broad tasks touching `runner.py` and `cli.py` encouraged invalid rewrites even when tests eventually went green.

## Run order

Execute these subtasks in order from clean `main`:

1. `tasks/038a_orchestrator_run_loop_engine.md`
2. `tasks/038b_orchestrator_run_loop_cli_surface.md`
3. `tasks/038c_orchestrator_run_loop_decision_logging.md`

Do not skip ahead.

## Why it was split

- `runner.py` is a fragile, high-contract file and must be changed additively only
- CLI wiring and decision logging are separable from the engine loop
- smaller tasks make protected-file policies enforceable by both the prompt and `run_task.py`

## Current baseline assumptions

- Task 037 is complete and green on `main`
- current `src/builder/orchestrator/runner.py` is the locked baseline
- `tasks/state.json` is ignored runtime state and should be deleted before agent runs if present

## Acceptance gate before moving to Task 039

Do not begin Task 039 until:

- 038a is green and merged
- 038b is green and merged
- 038c is green and merged
- local `main` is refreshed from remote
