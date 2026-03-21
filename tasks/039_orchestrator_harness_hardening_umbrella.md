# Task 039 — Harness Hardening Tranche (Umbrella)

## Status

Do NOT run this umbrella task directly with the agent.

This workstream exists because the harness is now strong on bundle structure and policy enforcement, but still needed two more validation layers:

1. protected method edit engine coverage
2. protected API semantic preflight coverage
3. machine-readable contract coverage

## Current tranche shape

This tranche is now a mix of:
- one completed harness-validation task (`039a`)
- two remaining validation tasks (`039b`, `039c`)

The goal is to validate the current hardened harness, not to keep rewriting `agents/run_task.py` through task-driven self-modification.

## Run order

Execute these subtasks in order from clean `main`:

1. `tasks/039a_orchestrator_protected_method_edit_engine.md`
2. `tasks/039b_orchestrator_protected_api_semantic_preflight.md`
3. `tasks/039c_orchestrator_machine_readable_task_contracts.md`

After all three are green and merged:

4. `tasks/040_orchestrator_end_to_end_integration_harness.md`
5. `tasks/041a_orchestrator_project_config_schema.md`
6. `tasks/041b_orchestrator_multi_project_adapter_tests.md`

## Current baseline assumptions

- Task 037 is complete and green on `main`
- Tasks 038a / 038b / 038c are complete and green on `main`
- Task 038d is complete and green on `main`
- Task 039a is complete and green on `main`
- Task 040 was previously blocked more by harness validation drift than by the production orchestrator logic itself

## Acceptance gate

Do not mark Task 039 complete until all of 039a / 039b / 039c are green and merged.
