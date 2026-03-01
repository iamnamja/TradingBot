# Task 004: Data layer (quotes/bars + caching)

## Goal
Create a unified data interface for:
- latest quote/price
- recent bars (e.g., last 50 5-min bars)
- simple caching to reduce API calls

## Scope
- Implement `DataClient` interface
- Alpaca implementation: `AlpacaDataClient`
- Methods:
  - `get_latest_price(symbol) -> float`
  - `get_bars(symbol, timeframe, limit) -> DataFrame|list`
- Add basic in-memory cache with TTL (e.g., 30s)

## Acceptance Criteria
- Data layer can fetch latest price for configured tickers (paper ok)
- Strategy can call data layer without knowing broker details
- Unit tests can run without network calls (mock client)

## Tests
- Unit test for cache hit/miss behavior
- Unit test for DataClient interface usage (mocked)

## Notes for Agents
- Don’t couple this to trading/execution
- Keep return shapes consistent and documented