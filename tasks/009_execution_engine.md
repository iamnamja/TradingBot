# Task 009: Execution engine (orders)

## Goal
Place orders for approved candidates through broker adapter (Alpaca first).

## Scope
- Broker interface:
  - `submit_order(symbol, qty, side, type, limit_price=None)`
  - `get_account()`
  - `get_positions()`
- Execution engine responsibilities:
  - translate candidate -> order
  - handle dry_run (log only)
  - handle order confirmation/polling (optional v1)

## Acceptance Criteria
- In `DRY_RUN=true`, no orders are sent
- In `DRY_RUN=false`, orders submit successfully (paper)
- Logs order_id + status

## Tests
- Unit tests with mocked broker
- No live API calls in CI