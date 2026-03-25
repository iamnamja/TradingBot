# Task 052 — Orchestrator Second Project Portability Proof

## Goal

Prove that the orchestrator can bootstrap and reason about a second non-TradingBot project fixture without relying on TradingBot-specific assumptions, **without regressing the post-050 public/bootstrap compatibility surface**.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `tests/fixtures/sample_app/project_config.json`
- `tests/fixtures/sample_app/tasks/001_sample_task.md`
- `tests/test_second_project_portability.py`

## Harness policy

- FILE: tests/test_second_project_portability.py MODE=TESTS_ONLY

## Required behavior

1. add a minimal second project fixture that is clearly not TradingBot-specific
2. prove bootstrap/config/adapter behavior works against that fixture
3. prove validator selection and protected-file settings come from the fixture config/adapter, not TradingBot hardcoding
4. make the portability proof fixture-local and self-contained; it should not depend on TradingBot repo paths, TradingBot task names, or TradingBot package assumptions

## Critical compatibility constraint

This task is **additive portability work**, not a redesign of the builder bootstrap layer.

The following existing public/bootstrap helpers must remain present and importable after this task:

### In `src/builder/orchestrator/project_config.py`
- `ProjectConfig`
- `GenericProjectConfig`
- `load_project_config`
- `bootstrap_project_config_scaffold`

### In `src/builder/orchestrator/project_adapter.py`
- `ProjectAdapter`
- `load_project_adapter`
- `bootstrap_project_adapter_scaffold`
- `build_bootstrap_starter_docs_text`
- `build_bootstrap_task_template_text`

Do not delete, rename, inline away, or relocate those helpers.

## Existing contract preservation

This task must preserve the current post-050 compatibility contracts, including:

- TradingBot defaults in `ProjectAdapter.get_tradingbot_default_config()`
- Generic defaults in `ProjectAdapter.get_generic_project_config()`
- existing bootstrap scaffold helpers used by current tests
- existing import locations expected by:
  - `tests/test_project_bootstrap_adapter.py`
  - `tests/test_validator_plugins.py`
  - `tests/test_project_adapter.py`

The second-project portability proof must be layered on top of those contracts, not replace them.

## Portability constraints

The portability proof should explicitly avoid assumptions such as:

- hardcoded `TradingBot` project names
- hardcoded TradingBot task directories or repo-root layout
- TradingBot-only validator or protected-file defaults
- hidden dependence on app-specific paths when running the fixture test from a temporary copied directory

## Implementation guidance

- extend the config/adapter layer to support the fixture
- keep bootstrap helpers and legacy exports intact
- keep portability proof fixture-local and test-driven
- prefer additive helpers or compatibility-preserving refactors over replacing existing functions

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `tests/test_second_project_portability.py` proves the engine can reason about the second project fixture
- no TradingBot-specific path assumptions are required for the second project test to pass
- the test demonstrates that validator selection and protected-file settings originate from the fixture config/adapter path, not TradingBot hardcoding
- existing bootstrap/adapter/import-based tests remain green
