# Task 010: End-to-end cycle runner + logging/audit

## Goal
Create a single “cycle” runner that:
- checks market hours
- fetches data using the existing data-layer interface
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

## Required repo alignment

### Data layer alignment
Task 004 defines `DataClient` in:
- `from tradingbot.data.client import DataClient`

And its interface methods are:
- `get_latest_price(symbol: str) -> float`
- `get_bars(symbol: str, timeframe: str, limit: int) -> list[Bar]`

For this task:
- Do **not** invent `fetch_data()`
- Do **not** mock `fetch_data()`
- The cycle runner and tests must use the actual Task 004 data-layer interface

### Strategy alignment
Task 006 defines:
- `StrategyV1.generate(symbols: list[str], data: DataClient, cfg: Settings) -> list[Candidate]`

The cycle runner should call the strategy layer instead of re-implementing candidate generation logic.

### Execution alignment
Task 009 defines the execution layer.
The cycle runner should use the existing execution abstraction and must not place orders directly.

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
- use fakes/mocks for `DataClient`, `LLMAdvisor`, `RiskGate`, and the execution layer
- mock the actual `DataClient` interface methods from Task 004:
  - `get_latest_price`
  - `get_bars`
- assert returned dict shape
- assert an audit artifact is created
- assert the audit path directory exists
- no live external calls in tests

## Bundle requirement
The output bundle must include all required deliverables:
- `src/tradingbot/cycle/runner.py`
- `src/tradingbot/logging/audit.py`
- `tests/test_cycle_runner_smoke.py`

Do not omit any required file on retry attempts.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- running a cycle in dry-run mode produces an audit artifact in `logs/`
- `write_audit()` creates the log directory if missing
- the implementation aligns with:
  - Task 004 data-layer interface
  - Task 006 strategy interface
  - Task 009 execution abstraction
