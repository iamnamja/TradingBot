# Task 201 — orchestrator supervised three-step canary runner and chain ledger

## Why

Task 199 admitted a supervised three-step canary contract, but that truth is still only a contract surface. The repo now needs a real exactly-three-task execution seam so the canary shape is not just theoretical.

## Scope

Add a real supervised three-step canary runner for exactly three adjacent tasks and persist a durable chain ledger.

## Runtime seams to reuse

- Reuse adjacent-pair admission and handoff truth from the bounded two-task pilot.
- Reuse supervision and no-manual-intervention truth from bounded pilot artifacts.
- Reuse resume-truth vocabulary from Task 198.
- Reuse artifact directory and ledger naming discipline already used by the bounded two-task path.

## Requirements

- Accept exactly three tasks in a canary run.
- Require all three tasks to be explicitly admitted.
- Require strict adjacency:
  - `B.follows == A.id`
  - `C.follows == B.id`
- Keep the runner supervised-only.
- Persist a durable chain ledger that records at minimum:
  - chain/session id,
  - task ids and task order,
  - adjacent pair truth for A->B and B->C,
  - supervision truth,
  - resume truth per adjacent pair,
  - terminal chain outcome.
- Keep the runner bounded to exactly three tasks only.

## Create or update these exact files

- `agents/lib/three_step_canary.py`
- `tests/test_three_step_canary.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/201_orchestrator_supervised_three_step_canary_runner_and_chain_ledger.md`

## Non-goals

- Do not support arbitrary-length manifests.
- Do not widen beyond the explicit supervised three-step canary shape.
- Do not replace the bounded two-task pilot runner.

## Acceptance criteria

- Tests prove the runner accepts exactly three adjacent tasks and rejects broader or malformed shapes conservatively.
- Tests prove durable chain ledgers are written and include admission, adjacency, supervision, and resume truth.
- Tests prove blocked or incompatible chains stop explicitly rather than continuing.
