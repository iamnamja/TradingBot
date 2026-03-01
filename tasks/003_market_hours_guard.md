# Task 003: Market hours guard

## Goal
Prevent accidental trading outside US equities market hours (initially).

## Scope
- Implement `market_hours_guard(now, calendar_source)` that returns:
  - `is_open: bool`
  - `reason: str`
- Initially: simple guard using weekday + time window
- Later: upgrade to broker calendar / exchange calendar

## Initial Rules (simple)
- Only allow trading Mon–Fri
- Only allow trading 9:30am–4:00pm America/New_York
- Optional: allow pre/post market via config flags later (not now)

## Acceptance Criteria
- When market is closed:
  - bot logs “market closed” and exits cleanly (or sleeps if scheduled mode later)
- When open:
  - bot continues

## Tests
- Unit tests for boundary times:
  - Mon 9:29 -> closed
  - Mon 9:30 -> open
  - Mon 16:00 -> closed (or open until 16:00 exclusive—define precisely)
  - Sat noon -> closed

## Notes for Agents
- Use timezone-aware datetime (America/New_York)
- Avoid system locale pitfalls; explicitly set tz