# Task 173 — orchestrator supervised dev-test role split for bounded pilot

## Why

The long-term goal is for the orchestrator to know when a dev agent should act next, when a test agent should validate, and how bounded repair should happen without collapsing into a monolithic lane. We should start with the smallest supervised pilot version of that split.

## Scope

Introduce an explicit supervised dev/test role split for bounded two-task pilot work.

## Requirements

- Reuse the existing multi-agent surfaces where possible.
- Define when the dev role acts, when the test role acts, and when the controller must stop rather than improvise.
- Keep the role split bounded to the pilot lane; do not claim general multi-agent autonomy yet.
- Persist role decisions or checkpoints so later pilot re-proofs can audit them.

## Create or update these exact files
- agents/lib/multi_agent_contract.py
- agents/lib/multi_agent_loop.py
- tests/test_orchestrator_integrated_capabilities.py
- tasks/173_orchestrator_supervised_dev_test_role_split_for_bounded_pilot.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove the pilot lane distinguishes dev and test roles explicitly.
- Tests prove the controller stops conservatively when the role sequence is unsupported.
- Docs explain that this is supervised role separation, not broad autonomous multi-agent execution.
