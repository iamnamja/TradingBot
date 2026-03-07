# Task 011: Alpaca broker adapter (paper-first)

## Goal
Implement a real Alpaca-backed broker adapter that satisfies the existing broker abstraction and can be used for paper trading.

## Deliverables
- `src/tradingbot/brokers/alpaca.py`
  - `class AlpacaBroker`
  - must satisfy the existing broker protocol from:
    - `from tradingbot.brokers.base import Broker`

- `tests/test_alpaca_broker.py`

## Existing repo dependencies (not deliverables)
These files already exist in the repo and must be reused, not recreated:
- `src/tradingbot/brokers/base.py`
- `src/tradingbot/execution/engine.py`
- `src/tradingbot/execution/types.py`

Do **not** include the dependency files above in the output bundle unless the task truly requires modifying them.

## Required repo alignment
- Use the existing broker protocol from Task 009
- Do **not** bypass the execution engine
- Do **not** redefine the `Broker` protocol
- Keep this task focused on the Alpaca adapter only

## Required behavior

### Constructor
`AlpacaBroker` should accept enough configuration to work in paper mode.

Suggested constructor:
- `__init__(self, api_key: str, api_secret: str, paper: bool = True)`

Behavior:
- initialize the Alpaca `TradingClient` internally
- store enough state on the adapter to make testing easy
- it is acceptable and encouraged to store:
  - `self.paper = paper`

### submit_order
Implement:

```python
submit_order(self, symbol: str, qty: int, side: str) -> dict
```

Behavior:
- submit a market order
- support only `buy` and `sell`
- return a simple structured dict containing at least:
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
- market orders only
- no advanced order types yet

## Test requirements
`tests/test_alpaca_broker.py` must:
- not make live external calls
- patch `alpaca.trading.client.TradingClient`
- mock the constructed client instance correctly
- verify:
  - valid order submission returns the expected dict shape
  - invalid side raises or returns explicit error
  - invalid qty raises or returns explicit error
  - paper mode is passed correctly to the Alpaca client constructor

## Important test guidance
- Do **not** assert `alpaca_broker.client.paper`
  - the real Alpaca client may not expose `.paper` as an attribute
- Instead, use one of these acceptable assertions:
  - assert the patched `TradingClient` constructor was called with `paper=True`
  - or assert `alpaca_broker.paper is True` if the adapter stores that field

- Do **not** create unused fixture variables such as:
  - `with patch(...) as mock_client:` unless `mock_client` is actually used
- If you need the patched constructor mock, use it explicitly in the test body

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- `AlpacaBroker` satisfies the existing `Broker` protocol
- tests do not require real Alpaca credentials
- tests do not make live network calls
