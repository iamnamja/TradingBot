# Task 050 — Orchestrator Public Interface Freeze

## Goal

Freeze the public orchestrator surface so the product can later move to its own package/repository without ambiguous boundaries.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `ORCHESTRATOR_PRODUCT_SPEC.md`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `ORCHESTRATOR_VISION_AND_CONTROLS.md`
- `agents/run_task.py`
- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `agents/lib/validator_runner.py`
- `tests/test_orchestrator_public_surface.py`

## Harness policy

- FILE: ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY
- FILE: ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY
- FILE: ORCHESTRATOR_VISION_AND_CONTROLS.md MODE=DOCS_ONLY
- FILE: tests/test_orchestrator_public_surface.py MODE=TESTS_ONLY
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND
- APPEND_SECTION: _bootstrap_exports

## Required behavior

Document and freeze the intended public/stable surface for:

- project config schema
- project adapter translation interface
- validator plugin interface
- task spec machine-readable contract directives
- shell public entrypoints / compatibility wrappers

## Critical compatibility requirement

This is an interface freeze task, not a redesign task.

Prefer additive documentation, typed surfaces, compatibility wrappers, and deterministic tests over broad engine behavior changes.

Do not change command-line behavior, repo wiring, routing flow, or import/bootstrap order merely to make the docs cleaner.

The frozen public surface must remain compatible with the post-049 shell baseline.

## Required implementation emphasis

- make the frozen surface explicit and named
- distinguish public/stable interfaces from internal implementation details
- favor narrow typed helpers, dataclasses, Protocol-style contracts, or well-documented adapters over hidden convention
- keep the frozen surface compatible with later extraction work
- freeze the currently exposed bootstrap compatibility wrappers already relied on by the shell baseline

## Specific shell freeze requirement

In `agents/run_task.py`, preserve existing shell behavior and expose a small explicit compatibility export section for the bootstrap wrappers.

The frozen shell compatibility surface for this task must keep these wrapper names importable and callable:

- `bootstrap_project_adapter_scaffold`
- `bootstrap_project_config_scaffold`

These wrappers may delegate to typed internals, but their names and callability must remain stable.

Do not refactor unrelated shell logic in this task.

## Specific test requirement

The dedicated public-surface test must be safe under normal pytest collection in this repository.

That means it must not assume `agents` is importable by default at collection time unless the test explicitly bootstraps repo root first.

Prefer one of these patterns:

- bootstrap repo root/path inside the test before importing `agents.*`
- import through already-supported repository paths
- validate the frozen public surface partly via source inspection when that is safer than eager import-time assumptions

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- a dedicated public-surface test verifies the frozen public interface
- docs explicitly distinguish public/stable interfaces from internal implementation details
- the frozen public surface includes the post-049 shell compatibility wrappers already used by the shell baseline
- the frozen public surface is sequence-aware and compatible with later extraction work
