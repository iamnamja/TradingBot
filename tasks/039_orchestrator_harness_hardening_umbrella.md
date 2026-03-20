# Task 039 — Harness Hardening Tranche (Umbrella)

## Status

Do NOT run this umbrella task directly with the agent.

Task 039a is now complete and green on `main`.

The remaining work in this tranche is no longer about teaching the harness how to edit itself from scratch. We now have a manually hardened `agents/run_task.py` baseline, so the next tasks should validate that hardened behavior with deterministic tests before moving on to the end-to-end orchestrator harness work.

## Why this tranche exists

Recent failures showed three recurring gaps:

1. protected-file edit behavior needed to be stabilized in the harness itself before asking the agent to extend it
2. protected Python API drift needed deterministic semantic preflight coverage
3. machine-readable task contracts needed direct harness enforcement plus deterministic coverage

## Updated run order

Execute these subtasks in order from clean `main`:

1. `tasks/039b_orchestrator_protected_api_semantic_preflight.md`
2. `tasks/039c_orchestrator_machine_readable_task_contracts.md`

After both are green and merged:

3. `tasks/040_orchestrator_end_to_end_integration_harness.md`
4. `tasks/041a_orchestrator_project_config_schema.md`
5. `tasks/041b_orchestrator_multi_project_adapter_tests.md`

## Current baseline assumptions

- Task 037 is complete and green on `main`
- Tasks 038a / 038b / 038c are complete and green on `main`
- Task 038d is complete and green on `main`
- Task 039a is complete and green on `main`
- `agents/run_task.py` now includes:
  - unified protected method target extraction
  - protected append and replace flows
  - protected Python semantic preflight
  - machine-readable contract directive parsing
  - direct enforcement for `FORBID_IMPORTS`, `FORBID_CALLS`, `ALLOWED_METHODS`, `CONSTRUCTOR`, `CONFIG_WRAPPER`, and `RESULT_KEYS`

## Acceptance gate

Do not mark Task 039 complete until both 039b and 039c are green and merged.
