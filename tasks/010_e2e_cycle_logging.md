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
  - `class CycleRunner`
  - `run_once() -> dict`

- `src/tradingbot/logging/audit.py`
  - `write_audit(event: dict, path: str = "logs/") -> str`

- `tests/test_cycle_runner_smoke.py`

## Required behavior

### Audit writer
`write_audit(event, path="logs/")` must:
- create the target directory if it does not already exist
- write exactly one audit artifact per run
- return the written file path as a string

Implementation choice:
- JSON lines or one JSON file per run is fine
- choose one simple format and document it in code/comments

### Cycle runner
`CycleRunner.run_once()` must:
- return a structured dict result
- always write an audit artifact for each run
- write an audit artifact even in dry-run mode
- include the audit file path in the returned result if convenient

### Logging fields (minimum)
The audit event must include:
- timestamp (UTC, timezone-aware)
- market_hours_guard result + reason
- candidates
- llm decisions
- risk decisions
- executed intents (or dry-run intents)
- any errors

### Time handling
- Use timezone-aware UTC timestamps
- Do not use `datetime.utcnow()`
- Prefer `datetime.now(timezone.utc)`

## Tests
`tests/test_cycle_runner_smoke.py` must:
- use fakes/mocks for `DataClient`, `LLMAdvisor`, `RiskGate`, `Broker`
- assert returned dict shape
- assert an audit artifact is created
- assert the audit path directory exists
- no live external calls in tests

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- running a cycle in dry-run mode produces an audit artifact in `logs/`
- `write_audit()` creates the log directory if missing
