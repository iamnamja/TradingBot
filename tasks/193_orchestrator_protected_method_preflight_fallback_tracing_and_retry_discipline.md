# Task 193 — orchestrator protected-method preflight, fallback tracing, and retry discipline

## Why

Protected-method mode failures are currently too opaque. Operators need to know why that mode was chosen, whether fallback was attempted, and what changed across retries.

## Scope

Instrument protected-method preflight and retry shaping with explicit trace artifacts.

## Runtime seams to reuse

- Reuse protected-method mode selection logic.
- Reuse Task 189 capability negotiation.
- Reuse Task 191/192 capture and transport failure artifacts.

## Requirements

- Persist a protected-method preflight trace that records:
  - why protected-method mode was selected,
  - whether the selected model supports the required transport,
  - whether fallback was attempted,
  - and what retry discipline was applied.
- Make retries explainable rather than opaque.
- Add tests for protected-method fallback and no-fallback scenarios.

## Create or update these exact files

- `agents/run_task.py`
- `tests/test_run_task_protected_method_edit_engine.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/193_orchestrator_protected_method_preflight_fallback_tracing_and_retry_discipline.md`

## Trace artifacts

Protected-method preflight and retry discipline must persist small, machine-readable JSON artifacts:

- `_last_protected_method_preflight.json`
  - selection rationale (why protected mode was chosen),
  - partition of required paths into protected vs normal,
  - capability negotiation snapshot for method insertion (including fallback attempted/applied),
  - protected-mode retry policy description.

- `_last_retry_discipline_trace.json`
  - most recent phase and retry index,
  - attempted phases,
  - fallback attempted/applied,
  - compact transport support snapshot,
  - pointers to sibling artifacts.

These are additive observability artifacts and do not change prior artifact formats or the acceptance flow.
