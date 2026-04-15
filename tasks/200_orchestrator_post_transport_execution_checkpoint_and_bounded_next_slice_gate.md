# Task 200 — orchestrator post-transport execution checkpoint and bounded next-slice gate

## Why

After Tasks 196-199, the repo needs another honest checkpoint: has the recovered runtime path held up well enough under execution reproof to justify planning a bounded next slice, or should the project stay in reproof mode longer?

## Scope

Record a durable post-transport execution checkpoint and bounded next-slice gate.

## Runtime seams to reuse

- Reuse one-task and bounded two-task benchmark artifacts.
- Reuse transport-health artifacts from Tasks 191-195.
- Reuse resume-truth and supervision-truth surfaces from Tasks 196-199.
- Reuse the conservative checkpoint style from Tasks 190 and 195.

## Requirements

- Produce a durable checkpoint that states whether the repo is:
  - not ready to widen further,
  - conditionally ready under supervision to plan a bounded next slice,
  - or ready only for the explicitly admitted three-step canary.
- Explicitly evaluate:
  - one-task reproof on the recovered runtime path,
  - bounded two-task refresh on the recovered runtime path,
  - adjacent-pair resume precision,
  - supervision truth on any three-step canary admission surface,
  - and recurring transport failure-family rates.
- Keep the verdict conservative.

## Create or update these exact files

- `src/builder/orchestrator/transport_health.py`
- `src/builder/orchestrator/model_transport_checkpoint.py`
- `tests/test_transport_health.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/200_orchestrator_post_transport_execution_checkpoint_and_bounded_next_slice_gate.md`

## Non-goals

- Do not claim unattended multi-task autonomy.
- Do not reopen standalone productization.
- Do not widen beyond what the checkpoint can defend honestly.

## Acceptance criteria

- A durable post-200 checkpoint artifact exists.
- The bounded next-slice verdict is explicit, conservative, and supervision-aware.
- Tests cover the checkpoint decision branches.
