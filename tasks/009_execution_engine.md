# Task 009: Execution engine (orders)

## Goal
Place orders for approved candidates through the broker adapter (Alpaca first).

## Deliverables
- `src/tradingbot/execution/types.py`
  - `@dataclass OrderIntent`:
    - `symbol: str`
    - `qty: int`
    - `side: Literal["buy","sell"]`
- `src/tradingbot/execution/engine.py`
  - `class ExecutionEngine`:
    - `execute(intents: list[OrderIntent], broker: Broker, cfg: Settings) -> list[dict]`
  - Must support `dry_run` (log/return intents, do not submit)

## Notes
- Use existing broker abstraction in your repo (do not import Alpaca directly here unless the broker adapter lives here).
- Keep error handling minimal but explicit; return structured results.

## Tests
- `tests/test_execution_engine.py`
  - Use a fake broker to capture intents and simulate responses

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- No live broker calls in tests
