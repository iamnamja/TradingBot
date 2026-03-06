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

### RSI (v1, simplified for deterministic strategy tests)
This task does **not** require a textbook or Wilder RSI.

Implement a **toy deterministic oscillator** with the following exact algorithm.

Normative pseudocode:

```python
def rsi(values, window=14):
    if window <= 0:
        return [None] * len(values)

    if len(values) <= 1:
        return [None] * len(values)

    if window > len(values) - 1:
        return [None] * len(values)

    result = [None] * len(values)

    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        if delta > 0:
            result[i] = 100.0
        else:
            result[i] = 0.0

    return result
```

Rules:
- `result[0]` must always be `None`
- positive delta => `100.0`
- zero delta => `0.0`
- negative delta => `0.0`
- `window` acts only as a minimum-history gate:
  - if `window > len(values) - 1`, return all `None`
  - otherwise begin output at index `1`

Required RSI examples:
- `rsi([1, 2, 3, 4, 5], 14) == [None, None, None, None, None]`
- `rsi([1, 2, 1, 2, 1], 2) == [None, 100.0, 0.0, 100.0, 0.0]`
- `rsi([1, 1, 1, 1], 2) == [None, 0.0, 0.0, 0.0]`

Implementation note:
- Correctness for this task is defined by matching the pseudocode and required examples exactly
- Do **not** implement a standard rolling/Wilder RSI for this task

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
- RSI normative examples:
  - `rsi([1, 2, 1, 2, 1], 2) == [None, 100.0, 0.0, 100.0, 0.0]`
  - `rsi([1, 1, 1, 1], 2) == [None, 0.0, 0.0, 0.0]`
- trend_up true/false cases
- edge cases for empty or too-short input

Test style requirements:
- Do not write assertions like `assert x == True` or `assert x == False`
- Use:
  - `assert x`
  - `assert not x`

Bundle requirement:
- The output bundle must include both:
  - `src/tradingbot/indicators.py`
  - `tests/test_indicators.py`
- Do not omit the test file on retry attempts

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- Indicators handle short series gracefully (return `None` where insufficient history)
- No external dependencies (numpy/pandas) required for v1
- Tests must use deterministic hand-made inputs only
- The RSI implementation must satisfy the normative pseudocode and examples exactly
