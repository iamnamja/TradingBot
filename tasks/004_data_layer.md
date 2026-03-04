# Task 004: Data layer (quotes/bars + caching)

## Goal
Create a unified, testable data interface for:
- latest price
- recent bars (e.g., last 50 5-min bars)
- a small in-memory cache to reduce repeated API calls within a single run

## Deliverables
### 1) Interfaces + types
- `src/tradingbot/data/types.py`
  - `@dataclass Bar` with fields: `ts`, `open`, `high`, `low`, `close`, `volume`
- `src/tradingbot/data/client.py`
  - `class DataClient(Protocol)` (or ABC) with:
    - `get_latest_price(symbol: str) -> float`
    - `get_bars(symbol: str, timeframe: str, limit: int) -> list[Bar]`

### 2) Alpaca implementation
- `src/tradingbot/data/alpaca_client.py`
  - `class AlpacaDataClient(DataClient)`
  - Reads API keys from existing settings (do not read `.env` directly here)
  - Uses alpaca-py **data** APIs (do not place orders here)

### 3) Cache wrapper
- `src/tradingbot/data/cache.py`
  - `class CachedDataClient(DataClient)`
  - Cache policy:
    - cache key includes (`method`, `symbol`, `timeframe`, `limit`)
    - TTL seconds is configurable (default 15–60s)
    - in-memory only; reset each process run

## Out of scope
- Persistent storage (SQLite, Redis, etc.)
- Complex rate limiting / retries (keep it minimal, but design for extension)

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- Unit tests cover:
  - cache hits/misses/TTL expiry (use a fake clock)
  - Alpaca client calls are mockable and not executed in tests
- The data layer returns deterministic `Bar` objects (no pandas dependency required)

## Notes
If you want a DataFrame later, add it in a follow-up task explicitly (and add pandas to requirements). Keep v1 lightweight.
