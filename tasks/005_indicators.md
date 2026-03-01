# Task 005: Indicators

## Goal
Compute a small initial set of indicators used for deterministic candidate generation.

## Initial Indicators (v1)
- SMA (fast/slow)
- RSI (14)
- Simple trend filter (price above SMA)

## Scope
- `indicators.py` with pure functions:
  - `sma(series, window)`
  - `rsi(series, window=14)`
- Indicator computation should not call APIs; it consumes bars from data layer

## Acceptance Criteria
- Given a known price series, indicators match expected values (approx)
- Deterministic and testable

## Tests
- Unit tests using fixed input arrays with expected outputs
- No network calls

## Notes for Agents
- Keep dependencies minimal (pandas optional)
- Ensure numerical stability for short series