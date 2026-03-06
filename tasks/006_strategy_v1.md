# Task 006: Strategy v1 (deterministic candidates)

## Goal
Generate BUY candidates using deterministic rules, long-only.

## Inputs
- bars + indicators per symbol
- config thresholds

## Deliverables
- `src/tradingbot/strategy/types.py`
  - `@dataclass Candidate`:
    - `symbol: str`
    - `score: float`
    - `reason: str`
    - `snapshot: dict` (selected indicator values used)

- `src/tradingbot/strategy/strategy_v1.py`
  - `class StrategyV1` with:
    - `generate(symbols: list[str], data: DataClient, cfg: Settings) -> list[Candidate]`

- `tests/test_strategy_v1.py`

## Required imports / repo alignment
- `DataClient` must be imported from:
  - `from tradingbot.data.client import DataClient`
- Do **not** import `DataClient` from `tradingbot.data.types`
- Strategy code must use the repo layout created by Task 004 and Task 005

## Candidate rules (v1, normative)
Keep it simple and deterministic.

BUY candidate if all of the following are true:
- `last_close > SMA(20)`
- `trend_up(closes, lookback=5)` is `True`

Notes:
- Do **not** gate candidate creation on RSI ranges for this task
- Task 005 defines RSI as a simplified deterministic oscillator, so it should not be used as a hard BUY filter here
- You may include RSI in the candidate snapshot and/or reason text, but it must not block a candidate that otherwise passes the rules above

## Score and reason
- Score can be a simple deterministic heuristic
- Suggested score:
  - positive distance above SMA(20), e.g. `(last_close - sma20) / sma20`
- `reason` should briefly explain why the candidate passed
- `snapshot` should include the key values used, such as:
  - `last_close`
  - `sma20`
  - `trend_up`
  - optionally `rsi14`

## Behavior requirements
- If a symbol has insufficient history, skip it safely
- If rules fail, do not emit a candidate
- Strategy must be deterministic given the same bars
- Strategy must not call broker/order code

## Tests
- `tests/test_strategy_v1.py`
  - Use a fake `DataClient` that returns deterministic bars
  - Validate:
    - no candidates when rules fail
    - candidate fields filled correctly when rules pass
    - upward-trending price history above SMA(20) produces a BUY candidate

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- Strategy does not call broker/order code
- Strategy is deterministic given the same bars
- The implementation must align with:
  - Task 004 data-layer structure
  - Task 005 simplified indicators behavior
