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
- shell compatibility export surface used by the current post-049 shell baseline

## Critical compatibility requirement

This is an interface freeze task, not a redesign task.

Prefer additive documentation, typed surfaces, compatibility wrappers, and deterministic tests over broad engine behavior changes.

Do not change command-line behavior, repo wiring, routing flow, import/bootstrap order, or shell entrypoint structure merely to make the docs cleaner.

The frozen public surface must remain compatible with the post-049 shell baseline and the existing bootstrap/config/validator tests already present in this repository.

## Required implementation emphasis

- make the frozen surface explicit and named
- distinguish public/stable interfaces from internal implementation details
- favor narrow typed helpers, dataclasses, Protocol-style contracts, or well-documented adapters over hidden convention
- keep the frozen surface compatible with later extraction work
- preserve existing public symbol locations and legacy compatibility behavior
- do not move frozen wrappers between modules in this task

## Specific shell freeze requirement

Do **not** rewrite or miniaturize `agents/run_task.py` in this task.

For this repository's current post-049 shell baseline, the frozen shell compatibility surface is the mapping exposed through `agents.run_task._bootstrap_exports()`.

The dedicated public-surface test should validate that this export mapping still contains and resolves the bootstrap compatibility names already relied on by the shell baseline, rather than requiring newly invented top-level attributes on `agents.run_task`.

In particular, the test should validate the current shell-compatible export mapping for:

- `bootstrap_project_adapter_scaffold`
- `bootstrap_project_config_scaffold`

Do not require `agents.run_task` to grow new top-level wrapper names in this task.

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

## Exact config/default compatibility requirement

Preserve the current generic project-config compatibility contract exactly.

The public/default behavior must continue to satisfy the existing repository tests for:

- `state_path is None`
- `audit_path is None`
- `task_file_pattern == "*.task.md"`

Do not change these defaults in this task.

## Exact bootstrap scaffold compatibility requirement

Preserve the existing bootstrap scaffold contract exactly.

The bootstrap scaffolding behavior must remain compatible with the existing repository tests, including:

- deterministic file locations and filenames
- existing scaffold return keys, including `docs`, `task_template`, and `task_example`
- expected scaffold text/content shape used by the current bootstrap tests

Do not rename those keys or shift the returned artifact contract in this task.

## Exact validator compatibility requirement

Preserve the current legacy validator compatibility behavior.

The public validator surface must remain green with the repository's existing validator tests, including compatibility around `run_checks()` and the default non-plugin path behavior.

This task may document and freeze that surface, but it must not break the current compatibility path.

## Specific test requirement

The dedicated public-surface test must be safe under normal pytest collection in this repository.

That means it must not assume `agents` is importable by default at collection time unless the test explicitly bootstraps repo root first.

Prefer one of these patterns:

- bootstrap repo root/path inside the test before importing `agents.*`
- import through already-supported repository paths
- validate the frozen public surface partly via source inspection when that is safer than eager import-time assumptions

## Existing test-suite compatibility requirement

This task must remain green with the repository's existing compatibility tests.

In particular, do not break the expectations currently encoded in the repository tests around:

- bootstrap adapter exports and scaffold helpers
- bootstrap config compatibility wrappers
- generic project config defaults
- validator compatibility behavior

The dedicated public-surface test added by this task is additive; it does not replace the existing repository tests.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- a dedicated public-surface test verifies the frozen public interface
- docs explicitly distinguish public/stable interfaces from internal implementation details
- `agents/run_task.py` remains unchanged by this task
- the dedicated public-surface test validates the current shell-compatible bootstrap mapping through `_bootstrap_exports()` rather than requiring new top-level shell names
- `bootstrap_project_config_scaffold` remains publicly owned by `src/builder/orchestrator/project_config.py`
- `bootstrap_project_adapter_scaffold`, `build_bootstrap_starter_docs_text`, and `build_bootstrap_task_template_text` remain publicly owned by `src/builder/orchestrator/project_adapter.py`
- generic project config defaults remain exact: `state_path is None`, `audit_path is None`, and `task_file_pattern == "*.task.md"`
- bootstrap scaffold compatibility remains exact, including `docs`, `task_template`, and `task_example`
- validator compatibility remains green, including legacy `run_checks()` behavior
- the frozen public surface is sequence-aware and compatible with later extraction work
