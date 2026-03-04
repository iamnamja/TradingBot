# Task 005: Indicators

## Goal
Compute a small initial set of indicators used for deterministic candidate generation.

## Inputs
- Bars from the data layer (`list[Bar]`), or a list of closes derived from bars.

## Deliverables
- `src/tradingbot/indicators.py` with pure functions (no API calls):
  - `sma(values: list[float], window: int) -> list[float | None]`
  - `rsi(values: list[float], window: int = 14) -> list[float | None]`
  - `trend_up(values: list[float], lookback: int = 5) -> bool`  
    (simple: last value > value[-lookback])

- `tests/test_indicators.py`
  - uses small hand-made series to validate values and edge cases

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- Indicators handle short series gracefully (return `None` where insufficient history)
- No external dependencies (numpy/pandas) required for v1
