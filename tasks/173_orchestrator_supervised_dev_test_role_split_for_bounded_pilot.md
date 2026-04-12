# Task 173 — orchestrator supervised dev-test role split for bounded pilot

## Why

The bounded two-task pilot should not rely on vague “multi-agent” language. The runtime already has an explicit role model — `controller`, `builder`, and `verifier` — and the pilot should reuse that model rather than inventing a second role taxonomy. The smallest credible next step is to make the builder/verifier split explicit for bounded supervised pilot work while preserving controller authority.

## Scope

Introduce an explicit supervised dev/test role split for bounded two-task pilot work by reusing the existing builder/verifier/controller model.

## Runtime seams to reuse

- Reuse the role taxonomy and handoff surfaces in `agents.lib.multi_agent_contract`.
- Reuse `agents.lib.multi_agent_loop` for role sequencing and controller authority.
- Reuse existing role-trace and artifact capture in `agents.run_single_task`.
- Do **not** add new autonomous role types for this task.

## Requirements

- Treat the pilot’s “dev” role as the existing `builder` role and the “test” role as the existing `verifier` role.
- Keep `controller` as the only role allowed to approve the next role transition.
- Make the pilot role sequence explicit and inspectable in artifacts or checkpoints.
- The runtime must stop conservatively when the requested role sequence is unsupported or when controller authority would be bypassed.
- Keep this split bounded to the supervised pilot lane; do **not** claim general autonomous multi-agent execution.

## Create or update these exact files
- agents/lib/multi_agent_contract.py
- agents/lib/multi_agent_loop.py
- agents/run_single_task.py
- tests/test_orchestrator_integrated_capabilities.py
- tests/test_single_task_runner.py
- tasks/173_orchestrator_supervised_dev_test_role_split_for_bounded_pilot.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove the bounded pilot lane distinguishes builder and verifier responsibilities explicitly.
- Tests prove the controller remains the sole authority for next-role decisions.
- Tests prove the runtime stops conservatively when an unsupported role sequence is requested.
- Docs explain that this is supervised builder/verifier separation for the bounded pilot, not broad autonomous multi-agent execution.
