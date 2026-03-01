# Task 006: Strategy v1 (deterministic candidates)

## Goal
Generate buy candidates using deterministic rules, long-only.

## Inputs
- bars + indicators per symbol
- configuration thresholds

## Candidate Rules (initial, configurable later)
Example:
- BUY candidate if:
  - price > SMA(20)
  - RSI(14) between 40 and 70
  - SMA(20) trending up over last N bars (optional)

Exit rules (initial)
- If already holding, candidate to exit if:
  - RSI > 75 (overbought) OR
  - price crosses below SMA(20)

## Outputs
`Candidate` objects:
- symbol
- action: BUY/SELL/HOLD
- confidence_score (0-1)
- rationale (string list)

## Acceptance Criteria
- Produces candidates for configured tickers
- Deterministic output given fixed input bars
- Unit tests cover at least 2 symbols with synthetic series

## Tests
- Strategy unit tests using mocked bars
- Verify candidate generation logic + rationale fields

## Notes for Agents
- Keep strategy pure; no order placement here