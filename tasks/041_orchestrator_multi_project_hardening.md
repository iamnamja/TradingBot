# Task 041 — Multi-Project Hardening (Umbrella)

## Status

Do NOT run this umbrella task directly with the agent.

This workstream was split to keep config/schema changes separate from adapter/runner validation.

## Run order

Execute these subtasks in order from clean `main`:

1. `tasks/041a_orchestrator_project_config_schema.md`
2. `tasks/041b_orchestrator_multi_project_adapter_tests.md`

## Current baseline assumptions

- Tasks 037–038 are complete and green on `main`
- Tasks 039a / 039b / 039c are complete and green on `main`
- Task 040 is complete and green on `main`
- both `runner.py` and `cli.py` are protected for this workstream
- primary work belongs in config/adapter code and tests

## Acceptance gate

Do not mark Task 041 complete until both subtasks are green and merged.
