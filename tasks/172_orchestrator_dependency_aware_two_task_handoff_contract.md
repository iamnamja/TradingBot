# Task 172 — orchestrator dependency-aware two-task handoff contract

## Why

A bounded two-task pilot is only credible if task B receives a deterministic and inspectable handoff from task A. The current runtime already has adjacent-task building blocks — `depends_on`, `next_task_may_proceed`, role/artifact envelopes, and the single-task supervised handoff artifact — but it does not yet express a bounded two-task pilot handoff contract explicitly.

## Scope

Define and validate a dependency-aware, adjacent-task handoff contract for bounded supervised two-task pilot runs.

## Runtime seams to reuse

- Reuse `TaskQueueItem.depends_on` and existing queue normalization in `agents.lib.task_queue`.
- Reuse the existing `next_task_may_proceed` truth already surfaced by verifier/controller/final-acceptance flows.
- Reuse the single-task supervised handoff artifact surface in `agents.run_single_task` instead of inventing an unrelated handoff file format.
- Reuse role/artifact envelope concepts in `agents.lib.multi_agent_contract` where they help describe the handoff payload.

## Requirements

- Model the minimum durable handoff between adjacent tasks A and B only.
- Distinguish at least:
  - handoff_ready,
  - handoff_incomplete,
  - handoff_incompatible.
- The contract must make explicit whether task B may proceed.
- The contract must record enough context to audit why task B was blocked, including dependency truth and any implicated paths or verification profile relevant to the handoff.
- The handoff artifact must be durable and inspectable after task A completes.
- Task B must not start when the required handoff truth is incomplete or incompatible.
- Do **not** widen to arbitrary multi-task chains or a general scheduler.

## Create or update these exact files
- agents/lib/task_queue.py
- agents/lib/multi_agent_contract.py
- agents/run_single_task.py
- tests/test_task_queue.py
- tests/test_single_task_runner.py
- tasks/172_orchestrator_dependency_aware_two_task_handoff_contract.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove task B cannot start when task A does not produce a handoff-ready result.
- Tests prove the handoff state is persisted and inspectable.
- Tests prove incompatible dependency or proceed-state truth is reported explicitly rather than collapsing into a generic stop.
- Docs explain that this is an adjacent bounded-pilot handoff contract, not broad multi-task chaining.
