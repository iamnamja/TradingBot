# Task 008: Risk gate

## Goal
Prevent trades that violate risk constraints.

## Initial constraints (v1)
- max position size USD (per trade)
- max open positions
- max trades per day (simple counter in memory for now)

## Deliverables
- `src/tradingbot/risk/types.py`
  - `@dataclass PortfolioState`:
    - `cash_usd: float`
    - `open_positions: dict[str, float]` (symbol -> position notional or qty)
    - `trades_today: int`
- `src/tradingbot/risk/risk_gate.py`
  - `class RiskGate`:
    - `evaluate(candidate: Candidate, state: PortfolioState, cfg: Settings) -> tuple[bool, str]`

## Tests
- `tests/test_risk_gate.py` with simple candidate/state combos:
  - deny when max positions reached
  - deny when trade size exceeds max
  - allow when within limits

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- Reasons are stable strings suitable for logging/auditing
