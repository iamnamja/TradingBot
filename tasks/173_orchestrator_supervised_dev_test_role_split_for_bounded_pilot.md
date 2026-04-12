# Task 173 — orchestrator supervised dev-test role split for bounded pilot

## Why

The project should not jump from one-task proving into a vague multi-agent story. The smallest honest next step is an explicit supervised role sequence in the bounded pilot lane so the controller knows when build work happens, when test validation happens, and when it must stop.

## Scope

Introduce an explicit supervised dev/test role split for bounded two-task pilot work using the repo’s current controller/builder/verifier surfaces.

## Starting point in the current repo

`agents.lib.multi_agent_contract` and `agents.lib.multi_agent_loop` already model controller, builder, and verifier role handoffs. Tighten that existing lane rather than inventing new broad agent families.

## Requirements

- Reuse the existing controller/builder/verifier surfaces where possible.
- Treat the builder role as the bounded pilot dev role and the verifier role as the bounded pilot test role.
- Define the supported supervised role sequence for the pilot lane and persist the checkpoints needed to audit it.
- The controller must stop conservatively rather than improvising whenever the requested role sequence or transition is unsupported.
- Persist enough role-trace truth for later pilot re-proofs to tell:
  - which role acted,
  - what the controller requested next,
  - whether the sequence stayed inside the bounded pilot contract,
  - where the controller stopped.
- Do not claim general multi-agent autonomy or arbitrary role choreography.

## Create or update these exact files
- agents/lib/multi_agent_contract.py
- agents/lib/multi_agent_loop.py
- tests/test_orchestrator_integrated_capabilities.py
- tasks/173_orchestrator_supervised_dev_test_role_split_for_bounded_pilot.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove the pilot lane distinguishes builder/dev and verifier/test roles explicitly.
- Tests prove the controller stops conservatively when an unsupported role sequence is requested.
- Tests prove role checkpoints remain inspectable for later pilot re-proof work.
- Docs explain that this is supervised role separation for the bounded pilot lane, not broad autonomous multi-agent execution.
