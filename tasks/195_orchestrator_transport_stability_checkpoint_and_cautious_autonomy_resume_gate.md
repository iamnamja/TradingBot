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

## Outcome (checkpoint)

A conservative transport-stability checkpoint is now recorded:

- Artifact: `_transport_stability_checkpoint.json`
- Verdict: conditionally ready under supervision
- Meaning:
  - A cautious bounded next slice may be planned only if it continues stabilizing transport behavior and observability.
  - Broad unattended multi-task autonomy and standalone productization remain blocked.

The evaluation explicitly covered:
- capture integrity via explicit empty-capture accounting,
- parser-path observability for bundle and protected-method flows,
- bounded protected-method fallback tracing,
- recurring failure-family rates across the corpus,
- preservation of the proven GPT file-bundle path established in Task 190.

## Operator notes

- Artifacts are additive and colocated with the transport-health benchmark:
  - `_transport_health_summary.json`
  - `_transport_failure_families.json`
  - `_transport_stability_checkpoint.json`
- Code-level entrypoints exposed:
  - `aggregate_transport_health(corpus)`
  - `evaluate_transport_stability_gate(summary, families, gpt_file_bundle_preserved=None)`
  - `write_transport_stability_checkpoint(base_dir, evaluation, evidence_snapshot=None)`
  - `compute_and_write_transport_stability(corpus, base_dir, gpt_file_bundle_preserved=None, evidence_snapshot=None)`
