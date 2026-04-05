# Task 099 — Orchestrator multi-agent portability proof sync

## Why this task exists

After tasks 090–098, the repo needs one synchronized proof-and-doc checkpoint for the post-089 tranche.

This should not invent a broader claim than the tests justify. It should simply synchronize the stronger multi-agent/portability proof slice with docs and the root repo posture.

## Outcome

Produce a synchronized multi-agent portability proof checkpoint and update the repo’s public posture honestly.

## Create or update these exact files

- `tests/test_multi_project_adapters.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `README.md`

## Required behavior

The synchronized proof should demonstrate only what the repo can actually back with deterministic tests, including at most:

1. controller/builder/verifier role separation
2. dependency-aware short-manifest planning
3. explicit verification-authority posture
4. second-project Python portability proof
5. honest consumer-boundary / extraction-prep posture

## Tests

Add or adjust deterministic proof tests that demonstrate:

1. the multi-agent role contract and loop remain stable
2. planner/routing/verification truth remain consistent together
3. second-project portability proof is still green
4. docs/README claims remain narrower than or equal to the test-backed proof

## Guardrails

- Keep the claim bounded to what the deterministic proof actually covers
- Do not claim arbitrary project creation for any language or task family
- Do not claim broad unattended scheduler autonomy
- Treat docs/README claim-deferral rules as still in force

## Acceptance

This task is complete when the repo has a synchronized, honest, deterministic proof checkpoint for the multi-agent portability tranche after Task 089.
