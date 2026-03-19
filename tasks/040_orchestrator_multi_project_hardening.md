# Task 040 — Multi-Project Hardening (Umbrella)

## Status

Do NOT run this umbrella task directly with the agent.

This workstream was split to keep config/schema changes separate from adapter/runner validation.

## Run order

Execute these subtasks in order from clean `main`:

1. `tasks/040a_orchestrator_project_config_schema.md`
2. `tasks/040b_orchestrator_multi_project_adapter_tests.md`

## Current baseline assumptions

- Tasks 037–039 are complete and green on `main`
- both `runner.py` and `cli.py` are protected for this workstream
- primary work belongs in config/adapter code and tests

## Acceptance gate

Do not mark Task 040 complete until both subtasks are green and merged.
