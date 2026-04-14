# Task 194 — orchestrator transport health benchmark and failure-family corpus

## Why

Once capture and failure artifacts improve, the repo needs a simple way to quantify whether transport health is getting better.

## Scope

Add a small transport-health benchmark and recurring failure-family corpus.

## Runtime seams to reuse

- Reuse Tasks 191–193 transport artifacts.
- Reuse existing reliability/benchmark style where appropriate.

## Requirements

- Produce additive transport-health artifacts that summarize:
  - run count,
  - empty-capture count,
  - bundle-parse failure count,
  - method-insertion failure count,
  - fallback count,
  - recurring failure-family counts.
- Keep it separate from trading/runtime metrics.
- Add tests for synthetic corpus inputs and artifact writing.

## Create or update these exact files

- `src/builder/orchestrator/transport_health.py`
- `tests/test_transport_health.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/194_orchestrator_transport_health_benchmark_and_failure_family_corpus.md`
