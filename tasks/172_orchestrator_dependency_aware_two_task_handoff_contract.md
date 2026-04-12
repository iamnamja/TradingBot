# Task 172 — orchestrator dependency-aware two-task handoff contract

## Why

A bounded supervised two-task pilot is only credible if task two starts from deterministic truth produced by task one. The repo already has role-handoff surfaces; now it needs an adjacent-task handoff contract for pilot sequencing.

## Scope

Define and validate a dependency-aware adjacent-task handoff contract for supervised bounded two-task pilot work.

## Starting point in the current repo

The repo already has role-handoff and artifact-envelope surfaces in `agents.lib.multi_agent_contract`, plus queue/gate logic in `agents.lib.task_queue`. Extend those seams rather than creating an unrelated task-transition system.

## Requirements

- Model the minimum durable handoff truth between task A and task B.
- Keep this bounded to adjacent supervised pilot work only; do not generalize to arbitrary multi-task chains.
- Distinguish at least these handoff states:
  - safe handoff,
  - incomplete handoff,
  - incompatible handoff.
- The canonical handoff artifact must be deterministic and JSON-serializable.
- The handoff artifact must capture, at minimum:
  - from-task path,
  - to-task path,
  - task-one completion/post-task truth,
  - compatibility truth for starting task two,
  - missing or incompatible requirements,
  - final handoff state.
- Task two must remain blocked unless the handoff state is explicitly safe.

## Create or update these exact files
- agents/lib/task_queue.py
- agents/lib/multi_agent_contract.py
- tests/test_task_queue.py
- tasks/172_orchestrator_dependency_aware_two_task_handoff_contract.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove task two cannot start when the required handoff truth is incomplete or incompatible.
- Tests prove the adjacent-task handoff artifact is persisted as stable, inspectable truth.
- Docs explain that this is an adjacent-task pilot contract, not a general multi-task scheduler.
