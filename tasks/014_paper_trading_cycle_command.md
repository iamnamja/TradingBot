# Task 014: Manual paper-trading cycle command

## Goal
Provide one command that runs a real end-to-end paper-trading cycle using:
- real broker adapter
- real account state loader
- existing strategy / LLM / risk / execution / audit pipeline

This is the milestone for the **first manual paper-money test**.

## Deliverables
- `src/tradingbot/paper/run_paper_cycle.py`
  - callable module or script entrypoint
  - `main() -> int`

- `tests/test_run_paper_cycle.py`

## Required repo alignment
This task must wire together the existing pieces from:
- Task 010 cycle runner
- Task 011 Alpaca broker adapter
- Task 012 portfolio/account state loader
- Task 013 position sizing + intent planner

Do **not** re-implement those subsystems inside this script.

## Required behavior

### Command behavior
The command should:
- load settings
- initialize Alpaca paper broker
- initialize the data client
- initialize strategy, llm advisor, risk gate, planner, execution engine, cycle runner
- run exactly one cycle
- print a concise summary
- exit with code `0` on success

### Safety rules
This command is paper-first.
Required behavior:
- must only run in paper mode
- if settings indicate live mode, fail fast with a clear message
- must respect dry-run if enabled

### Returned / printed information
At minimum, the command should make it easy to see:
- market-hours result
- candidate count
- approved/risk-passed count
- order intents created
- execution results
- audit file path

### Symbol scope
For this task, a small configured symbol list is sufficient.
Do not implement universe discovery here.

## Test requirements
`tests/test_run_paper_cycle.py` must:
- not hit real external services
- mock the initialized components
- verify:
  - paper-mode guard works
  - command returns success code on happy path
  - command prints/returns a useful summary shape

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- command refuses to run in live mode
- command is ready to be used for the first manual paper-trading cycle once real paper credentials are configured
