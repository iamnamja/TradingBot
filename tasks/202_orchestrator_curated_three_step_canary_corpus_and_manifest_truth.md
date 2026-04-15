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

## Deliverables

- Schema/loader module: `agents/lib/three_step_manifest.py`
- Tests: `tests/test_three_step_manifest.py`
- Docs state updates: `docs/TRADINGBOT_PROJECT_STATE.md`, `docs/README.md`

## Manifest schema

Top-level document:
- chains: array of chain objects

Chain object (canonical keys):
- id: string (chain id)
- tasks:
  - A: string (task id/path)
  - B: string (task id/path)
  - C: string (task id/path)
- adjacency:
  - A_to_B: boolean
  - B_to_C: boolean
  - reasons: object<string, string> (optional explanatory notes keyed by link)
- benchmark_eligible: boolean
- status: string enum
  - eligible | blocked | incompatible | supervision-heavy
- supervision: object (optional)
  - profile: string (e.g., light, operator-observed, heavy)
  - notes: string (optional)
- notes: string (optional)

Parser/loader expectations:
- Preserve truth exactly as written (no widening, no inference).
- Support round-trip serialization without losing fields.
- Provide helpers to:
  - filter positive/eligible chains (both adjacency links true, status eligible, and benchmark_eligible true),
  - list negative cases (blocked, incompatible, or supervision-heavy),
  - export a strict runner payload with exactly three tasks and adjacency booleans only.

## Corpus policy

- The curated set must include:
  - at least two positive/eligible chains,
  - and representative negative cases for blocked, incompatible, and supervision-heavy.
- Negative cases must include explanatory reasons for at least one rejected adjacency handoff.

## Implementation notes

- Add `agents/lib/three_step_manifest.py` with:
  - dataclasses for AdjacencyTruth, Supervision, ThreeStepChain, and ThreeStepManifest,
  - loaders from dict/file, strict JSON serializer,
  - positive/negative filters and a to_runner_payload that contains exactly three tasks and adjacency booleans.
- Provide `get_curated_manifest()` returning a built-in curated corpus,
  and `dump_curated_manifest(path)` to write it as JSON for inspection.

## Test plan

- Round-trip test: dump curated manifest to JSON, reload, and assert structural equality.
- Eligibility tests: verify positive/eligible vs negative chains are distinguishable and durable.
- Runner consumption seam: build a runner payload from an eligible chain and assert:
  - exactly three tasks are present in order A,B,C,
  - adjacency truth is preserved,
  - no extra fields implying widened scope are required by the seam.
  - additionally, import `agents.lib.three_step_canary` to assert the seam remains compatible.

## Non-goals

- Do not auto-discover arbitrary three-task chains from the backlog.
- Do not widen beyond curated explicit canary chains.

## Acceptance criteria

- Tests prove the manifest parser/loader preserves chain truth explicitly.
- Tests prove positive and negative canary chains are durable and distinguishable.
- Tests prove the three-step canary runner can consume the curated manifest without widening scope.

## Status

Schema keys finalized and curated corpus added with positive and negative examples. Loader and dumper support round-trip stability. Runner payload export preserves exactly-three adjacency for the canary runner seam.
