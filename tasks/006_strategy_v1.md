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

## Candidate rules (v1)
Keep it simple and configurable (suggested defaults):
- BUY candidate if:
  - last_close > SMA(20)
  - RSI(14) between [40, 70]
- Score can be a basic heuristic (e.g., distance above SMA, RSI midpoint)

## Tests
- `tests/test_strategy_v1.py`
  - Use a fake `DataClient` that returns deterministic bars
  - Validate:
    - no candidates when rules fail
    - candidate fields filled correctly when rules pass

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- Strategy does not call broker/order code
- Strategy is deterministic given the same bars
