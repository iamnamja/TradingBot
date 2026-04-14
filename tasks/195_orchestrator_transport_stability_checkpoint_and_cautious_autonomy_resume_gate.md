# Task 195 — orchestrator transport stability checkpoint and cautious autonomy-resume gate

## Why

After Tasks 191–194, the repo needs another honest checkpoint: has transport behavior become observable and stable enough to justify cautious next-slice planning, or should transport hardening continue first?

## Scope

Record a durable transport-stability checkpoint and cautious autonomy-resume gate.

## Runtime seams to reuse

- Reuse docs-status guarding from Task 186.
- Reuse model profiles and capability negotiation from Tasks 187 and 189.
- Reuse transport observability artifacts from Tasks 191–194.
- Reuse the existing conservative checkpoint style.

## Requirements

- Produce a durable checkpoint that states whether the repo is:
  - not ready to resume the next slice,
  - conditionally ready under supervision,
  - or ready to plan a cautious bounded next slice.
- Explicitly evaluate:
  - capture integrity,
  - parser-path observability,
  - protected-method fallback tracing,
  - recurring transport failure-family rates,
  - preservation of the proven GPT file-bundle path.
- Keep the verdict conservative.

## Create or update these exact files

- `src/builder/orchestrator/transport_health.py`
- `tests/test_transport_health.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/195_orchestrator_transport_stability_checkpoint_and_cautious_autonomy_resume_gate.md`
