# Task 064 — Orchestrator Safe Parallelism / Review Integration

## Goal

Deferred continuation task retained after the reliability/autonomy tranche.

Add focused integration coverage for safe-parallelism planning and protected-file review behavior using the **current live review contract**, without over-tightening optional semantics.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_safe_parallelism.py`
- `docs/ORCHESTRATOR_VISION_AND_CONTROLS.md`

## Harness policy

- FILE: tests/test_safe_parallelism.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_VISION_AND_CONTROLS.md MODE=DOCS_ONLY

## Required behavior

1. cover current live planner/review wiring for safe parallelism
2. preserve optional behavior where the live repo still treats some planner/review surfaces as best-effort
3. align protected-file review assertions to the current `run_review()` contract

## Review-contract guardrail

Tests may assert:
- presence of `mergeable`, `reasons`, and `warnings` keys
- specific values when the live repo clearly guarantees them

Tests must **not** require:
- `mergeable is False` in cases where the live repo does not guarantee that today
- non-empty `reasons` / `warnings` lists unless the live repo currently guarantees that

## Acceptance criteria

- `ruff check .` passes
- `pytest -q tests/test_safe_parallelism.py` passes
- safe-parallelism / review tests align with the current live contract instead of inventing stricter semantics
- the controls/vision doc reflects the current guarded/optional nature of the review flow
