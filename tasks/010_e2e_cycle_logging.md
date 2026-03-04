# Task 010: End-to-end cycle runner + logging/audit

## Goal
Create a single “cycle” runner that:
- checks market hours
- fetches data
- builds candidates
- LLM approve/veto (or noop)
- risk gate
- execute (or dry-run)
- writes an audit log per cycle

## Deliverables
- `src/tradingbot/cycle/runner.py`
  - `class CycleRunner`:
    - `run_once() -> dict`
- `src/tradingbot/logging/audit.py`
  - `write_audit(event: dict, path: str = "logs/") -> str`
  - JSON lines or single JSON file per run is fine; choose one and document it.

## Logging fields (minimum)
- timestamp (UTC)
- market_hours_guard result + reason
- candidates (pre + post LLM decisions)
- risk decisions
- executed intents (or dry-run intents)
- any errors

## Tests
- `tests/test_cycle_runner_smoke.py`
  - Wire fakes for DataClient, LLMAdvisor, RiskGate, Broker
  - Assert returned dict shape and that audit writer is called (or writes to temp dir)

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- Running a cycle in dry-run mode produces an audit artifact in `logs/` (or a temp dir in tests)
