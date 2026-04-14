# Task 191 — orchestrator raw model output capture integrity and non-empty artifact guarantee

## Why

Recent transport failures have shown a harmful ambiguity: the selected provider/model can be marked compatible while `_last_agent_model_output.txt` ends up effectively empty.

The repo needs a durable guarantee that transport failures either preserve non-empty raw output or explicitly record why capture is empty.

## Scope

Harden raw model-output capture integrity and persist an explicit capture result.

## Runtime seams to reuse

- Reuse provider/model capability diagnostics from Task 189.
- Reuse existing bundle and method-insertion transport error artifact flow.
- Reuse runtime-artifact hygiene and subset-preservation discipline.

## Requirements

- Persist a small explicit capture-result artifact for every transport failure.
- Distinguish at minimum:
  - non-empty raw output captured,
  - empty raw output captured,
  - capture failed before a payload was available,
  - raw output truncated or redacted for safety.
- Keep existing `_last_agent_model_output.txt` behavior, but make the emptiness case explicit rather than implicit.
- Add tests that cover zero-length, whitespace-only, and non-empty capture cases.

## Create or update these exact files

- `agents/run_task.py`
- `tests/test_bundle_transport_error_artifacts.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/191_orchestrator_raw_model_output_capture_integrity_and_nonempty_artifact_guarantee.md`

## Non-goals

- Do not widen autonomy claims.
- Do not redesign provider selection.
- Do not weaken parser strictness to hide capture bugs.

## Acceptance criteria

- Transport failures produce an explicit capture-result artifact.
- Empty raw output is classified clearly rather than implied by a one-byte file.
- Tests cover representative empty and non-empty capture outcomes.
