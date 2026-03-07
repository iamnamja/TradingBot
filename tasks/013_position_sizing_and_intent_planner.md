# Task 013: Position sizing + order intent planner

## Goal
Turn approved, risk-accepted candidates into concrete `OrderIntent` objects for execution.

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

## Existing repo dependencies (NOT deliverables)
The following modules already exist and must be reused rather than recreated:
- strategy types module under `src/tradingbot/strategy`
- execution types module under `src/tradingbot/execution`
- portfolio types module under `src/tradingbot/portfolio`
- settings module under `src/tradingbot/config`

Do not treat those existing modules as deliverables unless modification is truly required.

## Required repo alignment
- `Candidate` must come from:
  - `from tradingbot.strategy.types import Candidate`
- `OrderIntent` must come from:
  - `from tradingbot.execution.types import OrderIntent`
- `AccountState` and `PositionState` must come from:
  - `from tradingbot.portfolio.types import AccountState, PositionState`
- `Settings` must come from the actual project settings module:
  - `from tradingbot.config.settings import Settings`

Do **not** redefine these types.

## Required behavior

### PositionSizer
For v1, use a simple deterministic sizing rule.

Normative rule:
- target notional per trade = `cfg.max_position_size_usd`
- do **not** use a buying-power fraction for v1
- qty = `floor(cfg.max_position_size_usd / last_close)`
- if qty < 1, return `0`

Because `Candidate` may not contain `last_close` as a top-level field, read it from:
- `candidate.snapshot["last_close"]`

If `last_close` is missing, non-numeric, or not positive:
- return `0`

### Normative pseudocode
```python
def size_candidate(candidate, account, positions, cfg):
    last_close = candidate.snapshot.get("last_close")
    if last_close is None:
        return 0
    if last_close <= 0:
        return 0

    target_notional = cfg.max_position_size_usd
    qty = floor(target_notional / last_close)

    if qty < 1:
        return 0
    return qty
```

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
This task assumes the settings layer provides:
- `max_position_size_usd: float`

Use the existing field if already present.
If it is not present, add the minimum settings support required in the real settings module and tests.

## Test requirements
`tests/test_intent_planner.py` must verify:
- valid candidate produces one `OrderIntent`
- qty floors correctly
- candidate with missing `last_close` is skipped
- candidate with too-high price is skipped
- planner is deterministic

### Normative test examples
The implementation must satisfy these examples exactly:

Example 1:
- `cfg.max_position_size_usd = 1000`
- candidate `last_close = 100`
- expected qty = `10`

Example 2:
- `cfg.max_position_size_usd = 1000`
- candidate `last_close = 150`
- expected qty = `6`

Example 3:
- `cfg.max_position_size_usd = 1000`
- candidate `last_close = 2000`
- expected qty = `0` and candidate is skipped

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- output aligns with the existing execution layer
- no live broker/API calls in tests
- implementation matches the normative sizing rule and examples exactly
