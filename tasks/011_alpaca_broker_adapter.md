# Task 011: Alpaca broker adapter (paper-first)

## Goal
Implement a real Alpaca-backed broker adapter that satisfies the existing broker abstraction and can be used for paper trading.

## Deliverables
- `src/tradingbot/brokers/alpaca.py`
  - `class AlpacaBroker`
  - must satisfy the broker protocol from:
    - `from tradingbot.brokers.base import Broker`

- `tests/test_alpaca_broker.py`

## Required repo alignment
- Task 009 created:
  - `src/tradingbot/brokers/base.py`
  - `src/tradingbot/execution/engine.py`
  - `src/tradingbot/execution/types.py`
- This task must align with that existing execution layer.
- Do **not** bypass the execution engine.
- Do **not** redefine the `Broker` protocol.

## Required behavior

### Constructor
`AlpacaBroker` should accept enough configuration to work in paper mode.
Use the existing project settings layer where possible.

Suggested constructor pattern:
- accept credentials and `paper: bool`
- initialize the Alpaca trading client internally

### submit_order
Implement:

```python
submit_order(self, symbol: str, qty: int, side: str) -> dict
```

Behavior:
- submit a market order
- return a simple structured dict
- include at least:
  - `symbol`
  - `qty`
  - `side`
  - `status`
  - `order_id` if available

### Validation
- reject invalid `side` values outside `buy` / `sell`
- reject non-positive `qty`
- keep error handling minimal but explicit

### Paper-first scope
- this task is for paper trading readiness
- do not implement advanced order types yet
- market orders only are sufficient

## Test requirements
`tests/test_alpaca_broker.py` must:
- not make live external calls
- monkeypatch or mock the Alpaca client
- verify:
  - valid order submission shape
  - invalid side raises or returns explicit error
  - invalid qty raises or returns explicit error
  - paper flag is passed through correctly if applicable

## Notes
- The adapter must be mockable
- Keep the response format stable and simple
- No live API calls in tests

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- `AlpacaBroker` satisfies the existing `Broker` protocol
- tests do not require real Alpaca credentials
