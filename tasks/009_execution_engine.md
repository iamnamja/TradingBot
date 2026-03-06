# Task 009: Execution engine (orders)

## Goal
Place orders for approved candidates through a broker adapter (Alpaca will be implemented later).

## Deliverables

- `src/tradingbot/execution/types.py`
  - `@dataclass OrderIntent`
    - `symbol: str`
    - `qty: int`
    - `side: Literal["buy","sell"]`

- `src/tradingbot/execution/engine.py`
  - `class ExecutionEngine`
  - method:
    `execute(intents: list[OrderIntent], broker: Broker, cfg: Settings) -> list[dict]`
  - must support `dry_run` mode (log/return intents but do NOT submit orders)

- If no broker protocol/interface already exists in the repo, create:

  `src/tradingbot/brokers/base.py`

  with:

  ```python
  from typing import Protocol

  class Broker(Protocol):
      def submit_order(self, symbol: str, qty: int, side: str) -> dict: ...
  ```

  ExecutionEngine must import:

  ```python
  from tradingbot.brokers.base import Broker
  ```

## Notes

- ExecutionEngine must NOT import Alpaca directly.
- The broker adapter layer will handle exchange-specific logic.
- Error handling should be minimal but explicit.
- Return structured result objects (list of dict).

## Tests

- `tests/test_execution_engine.py`
- Use a fake broker implementation that records orders and returns dummy responses.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- No real broker calls occur during tests
