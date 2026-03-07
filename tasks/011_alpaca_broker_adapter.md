# Task 011: Alpaca broker adapter (paper-first)

## Goal
Implement a real Alpaca-backed broker adapter that satisfies the existing broker abstraction and can be used for paper trading.

## Deliverables
- `src/tradingbot/brokers/alpaca.py`
  - `class AlpacaBroker`
  - must satisfy the existing broker protocol

- `tests/test_alpaca_broker.py`

## Existing repo dependencies (NOT deliverables)
The following modules already exist in the repository and must be reused rather than recreated:
- the broker protocol module located at src/tradingbot/brokers/base.py
- the execution engine module located at src/tradingbot/execution/engine.py
- the execution types module located at src/tradingbot/execution/types.py

Important:
Do NOT treat the dependency modules above as deliverables. They must not be recreated unless modification is truly required.

## Required repo alignment
- Use the existing Broker protocol from the broker base module.
- Do not bypass the execution engine.
- Do not redefine the Broker protocol.
- This task should only implement the Alpaca adapter.

## Required behavior

### Constructor
`AlpacaBroker` should accept enough configuration to work in paper mode.

Suggested constructor:
    __init__(self, api_key: str, api_secret: str, paper: bool = True)

Behavior:
- initialize the Alpaca TradingClient internally
- store `self.paper = paper` so tests can verify the mode

### submit_order
Implement:

    submit_order(self, symbol: str, qty: int, side: str) -> dict

Behavior:
- submit a market order
- support only "buy" and "sell"
- return a dict containing at least:
  - symbol
  - qty
  - side
  - status
  - order_id if available

### Validation
- reject invalid side values outside buy / sell
- reject non-positive qty
- keep error handling explicit and simple

### Paper-first scope
- paper trading readiness only
- market orders only
- no advanced order types yet

## Test requirements
`tests/test_alpaca_broker.py` must:
- not make live external calls
- patch alpaca.trading.client.TradingClient
- mock the constructed client instance correctly

Verify:
- valid order submission returns expected dict shape
- invalid side raises or returns explicit error
- invalid qty raises or returns explicit error
- paper mode is passed correctly to the TradingClient constructor

## Important testing guidance
Do NOT assert that `alpaca_broker.client.paper` exists, because the real Alpaca client may not expose that attribute.

Acceptable checks:
- assert the patched TradingClient constructor was called with paper=True
- or assert alpaca_broker.paper is True

Avoid unused fixtures such as:
    with patch(...) as mock_client:
unless the mock variable is actually used.

## Acceptance criteria
- ruff check . passes
- pytest -q passes
- AlpacaBroker satisfies the existing broker protocol
- tests do not require real Alpaca credentials
- tests do not make live network calls
