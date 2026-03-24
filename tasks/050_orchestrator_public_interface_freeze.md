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
- HARNESS_POLICY: agents/run_task.py forbid

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

The frozen public surface must remain compatible with the post-049 shell baseline **and** the existing bootstrap adapter/config test suite already present in this repository.

## Required implementation emphasis

- make the frozen surface explicit and named
- distinguish public/stable interfaces from internal implementation details
- favor narrow typed helpers, dataclasses, Protocol-style contracts, or well-documented adapters over hidden convention
- keep the frozen surface compatible with later extraction work
- freeze the currently exposed bootstrap compatibility wrappers already relied on by the shell baseline
- preserve existing public symbol locations; do not move frozen wrappers between modules in this task

## Specific shell freeze requirement

Do **not** rewrite or miniaturize `agents/run_task.py` in this task.

The shell compatibility wrappers already relied on by the post-049 shell baseline are the public names that this task is freezing:

- `bootstrap_project_adapter_scaffold`
- `bootstrap_project_config_scaffold`

This task should freeze those names via docs and dedicated tests against the existing shell baseline, not by replacing the shell entry module.

If supporting tests need to reference the shell wrapper surface, they must validate the current exported behavior without broad shell refactors.

## Exact bootstrap symbol-to-module ownership requirement

Freeze the public bootstrap compatibility surface with the following exact module ownership:

### `src/builder/orchestrator/project_config.py`
This module remains the public owner of:

- `bootstrap_project_config_scaffold`

Do not move `bootstrap_project_config_scaffold` into `project_adapter.py` or any other module.

### `src/builder/orchestrator/project_adapter.py`
This module remains the public owner of:

- `bootstrap_project_adapter_scaffold`
- `build_bootstrap_starter_docs_text`
- `build_bootstrap_task_template_text`

Do not move these adapter-side symbols into `project_config.py` or any other module.

## Specific test requirement

The dedicated public-surface test must be safe under normal pytest collection in this repository.

That means it must not assume `agents` is importable by default at collection time unless the test explicitly bootstraps repo root first.

Prefer one of these patterns:

- bootstrap repo root/path inside the test before importing `agents.*`
- import through already-supported repository paths
- validate the frozen public surface partly via source inspection when that is safer than eager import-time assumptions

## Existing test-suite compatibility requirement

This task must remain green with the repository's existing bootstrap-related tests.

In particular, do not break or relocate the symbols expected by the existing bootstrap adapter/config tests. The dedicated public-surface test added by this task is additive; it does not replace the existing compatibility tests.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- a dedicated public-surface test verifies the frozen public interface
- docs explicitly distinguish public/stable interfaces from internal implementation details
- the frozen public surface includes the post-049 shell compatibility wrappers already used by the shell baseline
- `bootstrap_project_config_scaffold` remains publicly owned by `src/builder/orchestrator/project_config.py`
- `bootstrap_project_adapter_scaffold`, `build_bootstrap_starter_docs_text`, and `build_bootstrap_task_template_text` remain publicly owned by `src/builder/orchestrator/project_adapter.py`
- the frozen public surface is sequence-aware and compatible with later extraction work
