# Task 012: Portfolio/account state loader

## Goal
Load real account/position state needed for risk checks and paper-trading decisions.

## Deliverables
- `src/tradingbot/portfolio/types.py`
  - `@dataclass AccountState`
    - `cash_usd: float`
    - `equity_usd: float`
    - `buying_power_usd: float`

  - `@dataclass PositionState`
    - `symbol: str`
    - `qty: float`
    - `market_value_usd: float`

- `src/tradingbot/portfolio/loader.py`
  - `class PortfolioStateLoader`
  - method:
    - `load() -> tuple[AccountState, list[PositionState]]`

- `tests/test_portfolio_loader.py`

## Required repo alignment
- Task 008 introduced:
  - `src/tradingbot/risk/types.py` with `PortfolioState`
- This task should provide the runtime inputs needed to construct or derive the values used by the risk layer.
- Do **not** duplicate risk logic here.
- This task is about loading account + positions, not evaluating rules.

## Required behavior

### PortfolioStateLoader
The loader should depend on a broker/account source that can be mocked.

Suggested interface:
- initialize with a broker or client dependency
- call broker/client methods to fetch:
  - account summary
  - open positions

### Returned state
`load()` must return:
- `AccountState`
- `list[PositionState]`

### Notes on scope
- Keep it simple
- trades-today counting can remain separate if not naturally available here
- this loader should focus on current account + current open positions only

## Test requirements
`tests/test_portfolio_loader.py` must:
- use fake/mocked broker/account responses
- verify:
  - account fields are mapped correctly
  - positions are mapped correctly
  - empty positions case works
  - numeric fields are normalized to floats where reasonable

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- no live broker/API calls in tests
- output is suitable for feeding later risk and sizing logic
