# Task 041 — Multi-Project Hardening (Umbrella)

## Status

Do NOT run this umbrella task directly with the agent.

This workstream remains split so schema/config changes happen first, and multi-project runner validation happens only after the adapter/config baseline is green.

## Why this split matters

Recent 039/040 work showed that tasks converge much faster when:

- production engine changes are isolated to one narrow task
- later tasks become validation/tests-only tasks
- task specs pin the exact current baseline behavior instead of letting tests guess

This workstream follows that pattern.

## Run order

Execute these subtasks in order from clean `main`:

1. `tasks/041a_orchestrator_project_config_schema.md`
2. `tasks/041b_orchestrator_multi_project_adapter_tests.md`

## Current baseline assumptions

- Tasks 037–038 are complete and green on `main`
- Tasks 039a / 039b / 039c are complete and green on `main`
- Task 040 is complete and green on `main`
- `runner.py` and `cli.py` are protected for this workstream
- primary production work belongs only in config / adapter code for 041a
- 041b should validate the baseline produced by 041a without further engine edits

## Acceptance gate

Do not mark Task 041 complete until both subtasks are green and merged.
