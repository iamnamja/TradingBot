# Task 152 — Orchestrator one-task pass-rate scoreboard and failure digest

## Goal
Measure whether the orchestrator is actually getting better at autonomous one-task execution by tracking pass rate, retry rate, escalation rate, and dominant failure classes across the external-safe corpus.

## Scope
- one-task quality measurement only
- operator-facing score artifacts, not a broad app shell
- preserve truthful bounded claims

## Create or update these exact files
- `agents/lib/failure_journal.py`
- `agents/run_single_task.py`
- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `tests/test_single_task_runner.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_RELIABILITY_AND_AUTONOMY_REVIEW.md`
- `docs/README.md`

## Required behavior
The repo should emit a durable scoreboard or digest that summarizes external-safe corpus outcomes: completed without manual help, completed after self-heal, escalated, blocked by authority, and the dominant reasons for non-completion. The artifact should support a pass-rate target for the next re-proof task.

## Acceptance
This task is complete when operators can answer “how often does the bounded one-task lane really succeed on ordinary external-safe work?” from a durable artifact instead of from anecdotal task history.
