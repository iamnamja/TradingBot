# Task 008: Risk gate

## Goal
Prevent trades that violate risk constraints.

## Initial Constraints
- max position size USD (per trade)
- max open positions
- max trades per day
- max daily loss USD (later requires PnL tracking; start with a stub)

## Scope
- Implement `RiskGate.evaluate(candidate, portfolio_state) -> allow/deny + reason`
- Portfolio state includes:
  - open positions
  - recent trades count
  - cash/equity
- For now: implement position sizing + open positions + trades/day checks

## Acceptance Criteria
- Trades that exceed constraints are denied with clear reason
- Unit tests cover each constraint

## Tests
- RiskGate tests using synthetic portfolio states
- No broker dependency