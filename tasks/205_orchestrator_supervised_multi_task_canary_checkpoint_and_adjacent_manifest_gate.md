# Task 205 — orchestrator supervised multi-task canary checkpoint and adjacent-manifest gate

## Why

After Tasks 201-204, the repo needs another honest checkpoint: is the evidence strong enough to admit a tiny adjacent manifest under supervision, or should the project remain at one task plus bounded two-task and three-step canary proof only?

## Scope

Record a conservative post-canary checkpoint and decide whether a tiny adjacent-manifest gate may open under supervision.

## Runtime seams to reuse

- Reuse one-task, bounded two-task, and three-step canary benchmark artifacts.
- Reuse transport-health and post-200 checkpoint truth.
- Reuse supervision and resume-route truth from Tasks 201-204.

## Requirements

- Produce a durable checkpoint that states whether the repo is:
  - not ready to widen beyond the canary path,
  - conditionally ready under supervision for a tiny adjacent manifest,
  - or still limited to one-task plus bounded two-task and three-step canary proof only.
- The checkpoint must explicitly evaluate:
  - one-task stability,
  - bounded two-task stability,
  - three-step canary completion truth,
  - supervision/intervention rate,
  - controller-route and resume reconstruction stability,
  - transport-health stability.
- Keep the verdict conservative:
  - unattended multi-task autonomy remains blocked,
  - arbitrary scheduling remains blocked,
  - standalone productization remains blocked,
  - any admitted adjacent manifest must remain tiny, adjacent, curated, and supervised.

## Create or update these exact files

- `src/builder/orchestrator/multi_task_canary_checkpoint.py`
- `tests/test_multi_task_canary_checkpoint.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/205_orchestrator_supervised_multi_task_canary_checkpoint_and_adjacent_manifest_gate.md`

## Non-goals

- Do not claim unattended multi-task autonomy.
- Do not admit arbitrary manifests or open-ended role routing.
- Do not unblock standalone orchestrator-app work.

## Acceptance criteria

- A durable checkpoint artifact exists.
- Docs state clearly whether a tiny adjacent-manifest gate may open, and if so only under supervision.
- Blocked areas remain explicit.
- Scope honesty is preserved.
