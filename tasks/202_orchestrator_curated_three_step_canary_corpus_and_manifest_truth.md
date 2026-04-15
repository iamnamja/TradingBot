# Task 202 — orchestrator curated three-step canary corpus and manifest truth

## Why

A real three-step canary runner is only useful if it is exercised against an explicit, inspectable corpus. The repo needs a curated three-step manifest schema so canary evidence is reproducible and narrow.

## Scope

Create a curated three-step canary corpus and manifest format for supervised adjacent-chain runs.

## Runtime seams to reuse

- Reuse the exact three-step canary runner from Task 201.
- Reuse adjacent-pair admission and handoff truth already used in the bounded two-task pilot.
- Reuse benchmark and artifact naming conventions established in earlier bounded pilot work.

## Requirements

- Define a manifest schema for three-step canary chains.
- Each chain entry should persist at minimum:
  - chain id,
  - task A, B, and C paths/ids,
  - expected adjacency truth,
  - whether the chain is benchmark-eligible,
  - optional supervision profile or notes.
- Include both:
  - positive / eligible chains,
  - and negative cases such as blocked, incompatible, or supervision-heavy chains.
- Keep the corpus curated and explicit.

## Create or update these exact files

- `agents/lib/three_step_manifest.py`
- `tests/test_three_step_manifest.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/202_orchestrator_curated_three_step_canary_corpus_and_manifest_truth.md`

## Non-goals

- Do not auto-discover arbitrary three-task chains from the backlog.
- Do not widen beyond curated explicit canary chains.

## Acceptance criteria

- Tests prove the manifest parser/loader preserves chain truth explicitly.
- Tests prove positive and negative canary chains are durable and distinguishable.
- Tests prove the three-step canary runner can consume the curated manifest without widening scope.
