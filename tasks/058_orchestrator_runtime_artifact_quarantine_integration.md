# Task 053c — Orchestrator Runtime Artifact Quarantine Integration

## Goal

Add focused integration coverage for runtime artifact quarantine behavior using the **current live quarantine path and git-command behavior**, without assuming stricter exact command sequences than the repo guarantees today.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_runtime_artifact_quarantine.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: tests/test_runtime_artifact_quarantine.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY

## Required behavior

1. cover current runtime artifact quarantine integration behavior
2. align tests with the live helper behavior for unknown paths / cleanup commands
3. document the intended quarantine semantics clearly

## Quarantine-contract guardrail

Tests may assert:
- quarantine bookkeeping occurred
- expected file categories were considered
- git cleanup commands were issued in a way consistent with the current helper behavior

Tests must **not** require:
- one exact git-command sequence if the live helper currently permits a slightly different command shape
- quarantine invocation on failure paths where the current repo does not actually invoke it

## Acceptance criteria

- `ruff check .` passes
- `pytest -q tests/test_runtime_artifact_quarantine.py` passes
- quarantine tests align with the current live helper behavior
- controls/policies docs describe the supported quarantine contract clearly
