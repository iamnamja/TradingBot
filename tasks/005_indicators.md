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
    - simple rule: `last value > value[-lookback]`

- `tests/test_indicators.py`
  - uses small hand-made series to validate values and edge cases

## Indicator definitions (normative)

### SMA
- Return a list with the same length as `values`.
- For each index `i`:
  - if there are fewer than `window` values available up to `i`, return `None`
  - otherwise return the simple arithmetic mean of the last `window` values
- Example:
  - `sma([1, 2, 3, 4], 2) == [None, 1.5, 2.5, 3.5]`

### RSI (v1)
Use a simple non-Wilder RSI suitable for deterministic tests.

Definitions:
- Let `delta[i] = values[i] - values[i-1]` for `i >= 1`
- Gain for a delta = `max(delta, 0)`
- Loss for a delta = `abs(min(delta, 0))`

For each index `i >= 1`:
- If there is not enough history to compute the requested window according to the task tests, return `None`
- Otherwise compute RSI from the most recent deltas needed by the expected examples below

Behavior required by tests (these examples are normative):
- `rsi([1, 2, 3, 4, 5], 14) == [None, None, None, None, None]`
- `rsi([1, 2, 1, 2, 1], 2) == [None, 100.0, 0.0, 100.0, 0.0]`

Additional RSI rules:
- If average loss is `0` and average gain is positive, RSI = `100.0`
- If average gain is `0` and average loss is positive, RSI = `0.0`
- If both average gain and average loss are `0`, RSI = `50.0`
- Return values as floats

Note:
- The expected example above is the source of truth for this task. Implement the function so that the example passes exactly.

### trend_up
- Return `False` if there are fewer than `lookback` values
- Otherwise return:
  - `values[-1] > values[-lookback]`

Examples:
- `trend_up([1, 2, 3, 4, 5], 5) == True`
- `trend_up([5, 4, 3, 2, 1], 5) == False`

## Test expectations
The test file should include at least:
- SMA basic example
- RSI short-series behavior
- RSI normative example:
  - `rsi([1, 2, 1, 2, 1], 2) == [None, 100.0, 0.0, 100.0, 0.0]`
- trend_up true/false cases
- edge cases for empty or too-short input

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- Indicators handle short series gracefully (return `None` where insufficient history)
- No external dependencies (numpy/pandas) required for v1
- Tests must use deterministic hand-made inputs only
