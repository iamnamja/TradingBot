# Task 172 — orchestrator dependency-aware two-task handoff contract

## Why

A bounded two-task pilot is only credible if task two receives a deterministic handoff from task one. We need a durable adjacent-task contract so the orchestrator knows what can be handed forward and what must force a stop.

## Scope

Define and validate a dependency-aware handoff contract for adjacent supervised two-task pilot runs.

## Requirements

- Model the minimum durable handoff between task A and task B.
- Distinguish at least:
  - safe handoff truth,
  - incomplete handoff,
  - incompatible handoff.
- Persist the handoff truth in a durable artifact or state surface.
- Do not widen to arbitrary multi-task chains; this is for adjacent bounded pilot work only.

## Create or update these exact files
- agents/lib/task_queue.py
- agents/lib/multi_agent_contract.py
- tests/test_task_queue.py
- tasks/172_orchestrator_dependency_aware_two_task_handoff_contract.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove task two cannot start when the required handoff truth is incomplete or incompatible.
- Tests prove the handoff state is persisted and inspectable.
- Docs explain the adjacent-task handoff model.
