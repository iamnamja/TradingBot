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

Do not change command-line behavior, repo wiring, routing flow, import/bootstrap order, shell entrypoint structure, or bootstrap/export ownership merely to make the docs cleaner.

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

Preserve the current config/default compatibility contracts exactly.

### Generic project defaults
The public/default behavior for the generic project config must continue to satisfy the existing repository tests for:

- `state_path is None`
- `audit_path is None`
- `task_file_pattern == "*.task.md"`
- `artifact_path_patterns == ["generic_artifacts/*"]`
- `approval_required_file_patterns == ["README.md"]`

Do not change these defaults in this task.

### TradingBot defaults
The TradingBot-default config compatibility contract must continue to satisfy the existing repository tests, including:

- `task_file_pattern == "*.md"`

Do not change existing TradingBot default values in this task unless required solely to preserve current tests.

## Exact bootstrap scaffold compatibility requirement

Preserve the existing bootstrap scaffold contract exactly.

The bootstrap scaffolding behavior must remain compatible with the existing repository tests, including:

- deterministic file locations and filenames
- return values represented as `Path` objects where the current tests expect `Path`
- existing scaffold return keys, including:
  - `docs`
  - `task_template`
  - `task_example`
  - `adapter_factory`
  - `validator_config`
- expected scaffold text/content shape used by the current bootstrap tests

Do not rename these keys, remove them, or shift the returned artifact contract in this task.

### Exact starter-doc content requirement

The starter docs text produced by the adapter-side bootstrap helpers must remain compatible with the repository tests, including continued generic/reusable wording and continued reference to:

- `tasks/001_example_task.md`
- `task_template.md`

Do not remove those references in this task.

## Exact validator compatibility requirement

Preserve the current legacy validator compatibility behavior.

The frozen validator surface must remain compatible with the repository's existing validator tests, including compatibility around `run_checks()` and the default non-plugin path behavior.

This task may document and freeze that surface, but it must not break the current compatibility path.

### Exact legacy validator behavior to preserve

For the current repository baseline, the following default compatibility behavior is part of the frozen public surface:

- `load_project_config()` generic/default compatibility fallback must not inject plugin validator entries for the `config=None` path
- `select_validators(config=None)` must preserve the legacy non-plugin/default behavior
- `run_checks(config=None)` must preserve the legacy non-plugin/default path and must **not** activate plugin subprocess validators merely because a generic fallback config was synthesized
- plugin subprocess execution in this task must require an explicit project config / validator configuration, not the default compatibility path
- do not change `run_checks(config=None)` so that repository tests recursively shell out to `pytest -q`, `ruff`, or similar subprocess validators from inside normal pytest compatibility tests

Do not redefine the default compatibility path around validator plugins in this task.

### Exact validator plugin interface details to preserve

The repository's existing validator compatibility tests also rely on these concrete interface details remaining stable:

- `agents/lib/validator_runner.py` continues to expose module-level `subprocess`
- `run_checks(...)` continues to return `tuple[bool, str]`
- successful plugin validator execution continues to emit the compatibility output shape `"[<validator_name>] ok"`

Do not change these interface details in this task.

## Dedicated public-surface test constraint

The dedicated `tests/test_orchestrator_public_surface.py` test is intended to verify naming, ownership, and surface stability.

It is **not** the place to force plugin subprocess execution.

In particular:

- do not write the public-surface test so it relies on `run_checks(config=None)` spawning subprocess validators
- prefer source inspection, explicit import-time assertions, or monkeypatched/non-executing inspection of validator selection behavior over live recursive subprocess execution
- keep the dedicated public-surface test safe under normal pytest collection and repository test execution

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
- TradingBot default config expectations
- validator compatibility behavior
- bootstrap scaffold content, keys, and `Path`-typed return values

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
- generic project config defaults remain exact:
  - `state_path is None`
  - `audit_path is None`
  - `task_file_pattern == "*.task.md"`
  - `artifact_path_patterns == ["generic_artifacts/*"]`
  - `approval_required_file_patterns == ["README.md"]`
- TradingBot default config compatibility remains exact, including `task_file_pattern == "*.md"`
- bootstrap scaffold compatibility remains exact, including:
  - `docs`
  - `task_template`
  - `task_example`
  - `adapter_factory`
  - `validator_config`
- scaffold return values remain compatible with existing tests, including `Path`-typed expectations where present
- starter docs text remains generic/reusable and still references `tasks/001_example_task.md` and `task_template.md`
- validator compatibility remains green, including legacy `run_checks()` behavior
- `run_checks(config=None)` preserves the legacy non-plugin/default path and does not recursively trigger plugin subprocess validators
- `agents/lib/validator_runner.py` retains module-level `subprocess`, `run_checks(...) -> tuple[bool, str]`, and compatibility output shape `"[<validator_name>] ok"`
- the frozen public surface is sequence-aware and compatible with later extraction work
