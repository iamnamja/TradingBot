# Task 050 — Orchestrator Public Interface Freeze

## Goal

Freeze the public orchestrator surface so the product can later move to its own package/repository without ambiguous boundaries.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `ORCHESTRATOR_PRODUCT_SPEC.md`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `ORCHESTRATOR_VISION_AND_CONTROLS.md`
- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `agents/lib/validator_runner.py`
- `tests/test_orchestrator_public_surface.py`

## Harness policy

- FILE: ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY
- FILE: ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY
- FILE: ORCHESTRATOR_VISION_AND_CONTROLS.md MODE=DOCS_ONLY
- FILE: tests/test_orchestrator_public_surface.py MODE=TESTS_ONLY

## Required behavior

Document and freeze the intended public/stable surface for:

- project config schema
- project adapter translation interface
- validator plugin interface
- task spec machine-readable contract directives
- shell public entrypoints / compatibility wrappers

## Critical compatibility requirement

This is an interface freeze task, not a redesign task.

Prefer additive documentation, typed surfaces, and deterministic tests over broad engine behavior changes.

Do not change command-line behavior or repo wiring merely to make the docs cleaner.

## Required implementation emphasis

- make the frozen surface explicit and named
- distinguish public/stable interfaces from internal implementation details
- favor narrow typed helpers, dataclasses, Protocol-style contracts, or well-documented adapters over hidden convention
- keep the frozen surface compatible with the post-049 shell baseline

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- a dedicated public-surface test verifies the frozen public interface
- docs explicitly distinguish public/stable interfaces from internal implementation details
- the frozen public surface is sequence-aware and compatible with later extraction work
