# Task 039 — Harness Hardening Tranche (Umbrella)

## Status

Do NOT run this umbrella task directly with the agent.

This workstream exists because the harness is now strong on bundle structure and policy enforcement, but still too weak on live semantic/API validation. Repeated failures on the end-to-end harness showed that the agent can still drift on protected API surfaces even when the task is otherwise narrow.

## Why this tranche exists

Recent failures showed three recurring gaps:

1. the harness does not validate protected Python API contracts early enough
2. the harness depends too much on prose in task specs instead of machine-readable contracts
3. protected method edits still need one unified, reliable engine for append vs replace modes

## Run order

Execute these subtasks in order from clean `main`:

1. `tasks/039a_orchestrator_protected_api_semantic_preflight.md`
2. `tasks/039b_orchestrator_machine_readable_task_contracts.md`
3. `tasks/039c_orchestrator_protected_method_edit_engine.md`

After all three are green and merged:

4. `tasks/040_orchestrator_end_to_end_integration_harness.md`
5. `tasks/041a_orchestrator_project_config_schema.md`
6. `tasks/041b_orchestrator_multi_project_adapter_tests.md`

## Current baseline assumptions

- Task 037 is complete and green on `main`
- Tasks 038a / 038b / 038c are complete and green on `main`
- Task 038d is complete and green on `main`
- Task 040 was previously blocked by harness semantic drift, not by the production orchestrator logic itself

## Acceptance gate

Do not mark Task 039 complete until all of 039a / 039b / 039c are green and merged.
