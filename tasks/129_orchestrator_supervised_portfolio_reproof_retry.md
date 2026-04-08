# Task 129 — Orchestrator supervised portfolio re-proof retry

## Why this task exists

After the compatibility/self-heal/claim-discipline tranche lands, the orchestrator should rerun the bounded supervised multi-project portfolio proof and prove that the post-123 hardenings did not break the previously proven portfolio slice.

## Outcome

Rerun the bounded supervised multi-project portfolio proof after Tasks 124–128 land, while preserving project isolation, dependency-aware selection, hosted-authority truth, and conservative stop posture.

## Create or update these exact files

- `tests/test_project_registry.py`
- `tests/test_task_queue.py`
- `tests/test_multi_project_adapters.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_failure_journal.py`
- `tests/test_claim_discipline.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_ROADMAP_124_129.md`
- `docs/README.md`
- `README.md`

## Required behavior

The re-proof should remain explicitly bounded and demonstrate only:

1. supervised local-first portfolio progression across more than one registered project
2. preserved project-scoped state, branch, workspace, and carry-forward isolation
3. dependency-aware next-task selection and conservative stop posture
4. hosted-authority truth and merge-eligibility truth staying compatibility-preserving after Tasks 124–128
5. green-gated docs/status claim discipline for any proof-complete wording
6. no broader claim than the deterministic local supervised proof actually covers

Additional requirements:

- no new broad autonomy claims
- any new failure should be handled through the compatibility/self-heal contracts added in 124–128
- docs/status updates must remain green-gated and narrowly truthful
- do **not** return an empty file bundle; include the exact deliverables above even when updates are narrow

## Acceptance

- orchestrator-run Task 129 reaches green without manual recovery patching
- focused and full validation are green
- docs/state/spec claims match the proven deterministic supervised scope exactly
