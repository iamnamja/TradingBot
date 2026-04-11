# Task 167 — orchestrator authority corroboration and run truth

## Why

Even after the current reliability sprint, hosted-authority ambiguity still creates noise in the one-task lane. We need better corroboration so benchmark outcomes distinguish real authority blocks from timing artifacts without weakening conservative claim discipline.

## Scope

Improve authority corroboration and run-truth shaping while preserving the rule that unresolved authority ambiguity must not be silently treated as green.

## Requirements

- Reuse the existing hosted-authority and required-check truth surfaces where possible.
- Distinguish at least these cases inside benchmark/session artifacts:
  - likely CLI timing artifact,
  - unresolved authority ambiguity,
  - confirmed authority block.
- Persist the corroboration basis inside benchmark or re-proof artifacts.
- Keep the runtime conservative: unresolved ambiguity must not be treated as authority success.

## Create or update these exact files
- agents/run_task.py
- agents/lib/authority_gate.py
- tests/test_authority_gate.py
- tasks/167_orchestrator_authority_corroboration_and_run_truth.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove that benchmark artifacts record authority corroboration state.
- Tests prove that unresolved ambiguity still prevents false “ready to widen” claims.
- Docs explain the benchmark-time authority truth model.
