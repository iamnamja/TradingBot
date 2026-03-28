# Task 060 — Orchestrator Autonomy Loop Integration

## Goal

Integrate readiness, task-family routing, prompt compilation, seam validation, failure classification, localized repair, and PR/CI/merge handling into one orchestrator control loop.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/orchestrator_runtime.py`
- `tests/test_orchestrator_full_simulation_over_backlog.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_VISION_AND_CONTROLS.md`

## Harness policy

- FILE: tests/test_orchestrator_full_simulation_over_backlog.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY
- FILE: docs/ORCHESTRATOR_VISION_AND_CONTROLS.md MODE=DOCS_ONLY

## Required behavior

Demonstrate a loop that can:

- pick the next ready task
- choose the task-family lane
- compile the right request
- execute a task
- classify failures and choose remediation
- repair locally when safe
- manage PR/CI/merge outcomes
- advance backlog state deterministically

At least one simulated backlog run should recover from a deliberately introduced recoverable failure **without human intervention**.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- at least one simulated backlog run demonstrates the autonomy loop end-to-end and self-heals through a recoverable failure
