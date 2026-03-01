# Task 002: Config + settings (dotenv + validation)

## Goal
Centralize configuration with clear defaults, validation, and environment separation:
- paper vs live trading
- dry-run vs execute
- tickers list
- risk settings

## Scope
- Add `Settings` model (Pydantic recommended, but optional)
- Load `.env` via `python-dotenv`
- Support `.env.example` (safe to commit)
- Validate required fields for selected mode (paper/live)
- Provide clear startup log showing mode + key flags (never print secrets)

## Required Config Fields (initial)
### Broker / Alpaca
- `ALPACA_API_KEY`
- `ALPACA_API_SECRET`
- `ALPACA_BASE_URL` (paper default: `https://paper-api.alpaca.markets/v2`)
- `TRADING_MODE` = `paper` or `live`

### Runtime
- `DRY_RUN` = `true|false`
- `TICKERS` = comma-separated symbols (e.g. `SPY,QQQ,NVDA,GLD,SLV`)
- `LOG_LEVEL` = `INFO|DEBUG`

### Risk (initial)
- `MAX_POSITION_USD` = 500
- `MAX_DAILY_LOSS_USD` = 100
- `MAX_OPEN_POSITIONS` = 10
- `MAX_TRADES_PER_DAY` = 20

## Acceptance Criteria
- On startup, bot prints:
  - mode (paper/live)
  - dry_run
  - tickers count
  - risk limits summary
- Missing required env vars results in a friendly error message
- No secrets printed
- Tests validate config parsing + defaults

## Tests
- Unit test for Settings parsing
- Unit test verifying missing required vars raises error
- Unit test verifying defaults apply when env not set

## Notes for Agents
- Keep `.env` out of git; commit `.env.example` only
- In CI tests, set env vars in test process or use a minimal `.env.test`