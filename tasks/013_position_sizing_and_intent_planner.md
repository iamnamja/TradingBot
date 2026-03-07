# Task 013: Position sizing + order intent planner

## Goal
Turn approved/risk-accepted candidates into concrete `OrderIntent` objects for execution.

## Deliverables
- `src/tradingbot/planner/sizing.py`
  - `class PositionSizer`
  - method:
    - `size_candidate(candidate: Candidate, account: AccountState, positions: list[PositionState], cfg: Settings) -> int`

- `src/tradingbot/planner/intent_planner.py`
  - `class IntentPlanner`
  - method:
    - `build_intents(candidates: list[Candidate], account: AccountState, positions: list[PositionState], cfg: Settings) -> list[OrderIntent]`

- `tests/test_intent_planner.py`

## Required repo alignment
- Candidate type from:
  - `from tradingbot.strategy.types import Candidate`
- OrderIntent type from:
  - `from tradingbot.execution.types import OrderIntent`
- Account/positions types from:
  - `from tradingbot.portfolio.types import AccountState, PositionState`

Do **not** redefine these types.

## Required behavior

### PositionSizer
For v1, use a simple deterministic sizing rule.

Normative rule:
- target notional per trade = min(
  - configured max position size,
  - a fixed fraction of buying power if available
)
- qty = floor(target_notional / last_close)
- if qty < 1, do not trade that candidate

Because `Candidate` may not always contain `last_close` as a top-level field, the implementation should read it from:
- `candidate.snapshot["last_close"]`

If `last_close` is missing or invalid:
- return `0`

### IntentPlanner
`build_intents(...)` must:
- iterate candidates
- size each candidate
- skip zero-qty candidates
- emit `OrderIntent(symbol=..., qty=..., side="buy")`

For this task:
- long-only
- buy intents only
- no sell / rebalance logic yet

## Settings alignment
If the project settings already contain a max position size field, use it.
If not, add the minimum setting needed in the project settings layer and tests.

Suggested field:
- `max_position_size_usd: float`

## Test requirements
`tests/test_intent_planner.py` must verify:
- valid candidate produces one `OrderIntent`
- qty floors correctly
- candidate with missing `last_close` is skipped
- candidate with too-high price / too-small capital is skipped
- planner is deterministic

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- output aligns with the existing execution layer
- no live broker/API calls in tests
