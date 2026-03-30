# Task 070b — Orchestrator runtime artifact retention and visibility controls

## Why this task exists

The orchestrator currently writes scratch/debug artifacts such as `_last_agent_model_output.txt` and `_last_agent_file_bundle.txt` during execution, but successful pushed runs quarantine and remove them before staging.

That default safety behavior is reasonable, but the operator experience is still confusing:

- the files appear during a run
- then disappear on success
- and there is no explicit retention control for operators who want to keep them for forensic review

As backlog execution grows, operators need clearer and more intentional runtime-artifact lifecycle controls.

## Outcome

Keep the current runtime-artifact safety posture, but add explicit operator controls and clearer lifecycle messaging for known-safe scratch artifacts.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/artifact_quarantine.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_artifact_quarantine.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Preserve current default safety behavior

Successful `--push` runs should continue to quarantine/remove known-safe runtime scratch artifacts before staging so they do not accidentally get committed.

This includes current scratch files such as:

- `_last_agent_model_output.txt`
- `_last_agent_file_bundle.txt`
- other existing known-safe runtime artifacts already covered by the quarantine layer

### 2) Add explicit retention control

Provide a narrow operator control so known-safe runtime artifacts can be kept intentionally for debugging.

A flag and/or environment variable is acceptable, for example:

- `--keep-runtime-artifacts`
- `TRADINGBOT_KEEP_RUNTIME_ARTIFACTS=1`

The implementation should remain conservative and explicit.

### 3) Retained artifacts must still stay out of commits by default

When retention is enabled, the files may remain on disk after the run, but they still must not be staged/committed automatically by the controller.

### 4) Clear lifecycle messaging

The controller should tell the operator whether runtime artifacts were:

- retained intentionally
- quarantined and removed before staging
- blocked because an unknown runtime artifact was present

### 5) Preserve current failure-artifact behavior

Do not regress truthful failure-artifact persistence or unknown-artifact quarantine protections.

## Tests

Add coverage that proves:

1. known-safe runtime artifacts are removed on a successful push path by default
2. known-safe runtime artifacts are retained when the explicit control is enabled
3. retained artifacts are not accidentally staged by the controller
4. unknown runtime artifacts still trigger the existing protective behavior

## Documentation

Update the product spec and project-state docs to describe:

- the default quarantine/removal behavior for known-safe runtime artifacts
- the new operator retention control
- the distinction between safe retained scratch artifacts and blocked unknown artifacts

## Guardrails

- Do not disable runtime-artifact quarantine by default
- Do not silently keep scratch artifacts without an explicit operator signal
- Do not allow retained scratch artifacts to slip into automatic commits
- Prefer a narrow lifecycle-control improvement over a broad artifact-subsystem rewrite

## Acceptance

This task is complete when:

- default push behavior still quarantines known-safe scratch artifacts
- operators can explicitly retain those artifacts for debugging
- retained artifacts do not get auto-committed
- lifecycle messaging is clear and tests remain green
