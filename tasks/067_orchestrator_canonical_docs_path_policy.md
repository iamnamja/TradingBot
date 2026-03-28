# Task 067 — Orchestrator Canonical Docs Path Policy

## Goal

Deferred continuation task retained after the reliability/autonomy tranche.

Encode and enforce the repo’s canonical docs path conventions so future doc tasks stop drifting between repo root and `docs/`.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `tests/test_orchestrator_public_surface.py`
- `README.md`
- `docs/README.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: tests/test_orchestrator_public_surface.py MODE=TESTS_ONLY
- FILE: README.md MODE=DOCS_ONLY
- FILE: docs/README.md MODE=DOCS_ONLY
- FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY
- FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY

## Required behavior

1. codify the canonical location rules:
   - `README.md` stays at repo root
   - orchestrator/tradingbot narrative docs live under `docs/`
2. make those rules visible in docs and, where appropriate, in harness/path policy behavior
3. ensure future tasks have one unambiguous source of truth for doc placement

## Compatibility constraints

- do not move large sets of docs in this task unless needed for consistency
- do not create duplicate canonical docs in both root and `docs/`
- keep current valid post-051 docs layout intact

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- docs and/or harness policy clearly describe canonical doc placement
- the repo has an explicit policy that future tasks can follow
