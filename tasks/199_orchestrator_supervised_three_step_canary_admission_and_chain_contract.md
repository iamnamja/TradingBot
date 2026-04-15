# Task 199 — orchestrator supervised three-step canary admission and chain contract

## Why

If the recovered runtime path holds up under one-task and bounded two-task reproof, the smallest honest widening step is not broad autonomy. It is a narrowly admitted, explicitly supervised three-step canary chain.

## Scope

Define the admission and contract surface for a supervised three-step canary chain.

## Runtime seams to reuse

- Reuse adjacent-pair admission and handoff truth.
- Reuse supervision and no-manual-intervention accounting.
- Reuse transport-health and resume-truth artifacts from Tasks 191-198.

## Requirements

- Define a small supervised three-step chain contract, such as A->B->C.
- Keep admission explicit and narrow.
- Require supervision truth to remain first-class in the scorecard or ledger.
- Do not yet claim general three-task autonomy.

## Create or update these exact files

- `agents/lib/task_contracts.py`
- `agents/lib/multi_agent_contract.py`
- `tests/test_task_queue.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/199_orchestrator_supervised_three_step_canary_admission_and_chain_contract.md`

## Non-goals

- Do not run broad three-task autonomy.
- Do not remove supervision gates.
- Do not widen to arbitrary task chains.

## Acceptance criteria

- A supervised three-step canary admission contract exists.
- Supervision truth remains explicit and benchmark-visible.
- Tests cover contract acceptance and rejection conditions.
