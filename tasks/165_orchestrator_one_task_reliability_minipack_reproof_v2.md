# Task 165: orchestrator one-task reliability minipack re-proof v2

Goal

Re-run a small one-task reliability minipack after Tasks 162-164 and measure whether the second reliability sprint materially improved the one-task lane.

Why this matters

The first re-proof established that the project should stay in one-task reliability mode for another sprint. This task measures whether the second sprint is strong enough to keep using orchestrator-run mode by default for curated one-task work.

Create or update these exact files
- src/builder/orchestrator/benchmark.py
- src/builder/orchestrator/benchmark_scorecard.py
- tests/test_benchmark_scorecard_integration.py
- tasks/165_orchestrator_one_task_reliability_minipack_reproof_v2.md
- docs/TRADINGBOT_PROJECT_STATE.md

Scope
- Run the curated reliability minipack again using the current live benchmark and scorecard surfaces.
- Record strict scorecard totals.
- Surface the dominant remaining blocker families after the second sprint.
- Produce a short re-proof artifact with a conservative go / continue / no-go decision.

Acceptance criteria
- There is a durable re-proof artifact for the second minipack run.
- The artifact includes scorecard totals and dominant blocker families.
- The artifact states whether the project should remain in one-task reliability mode or can continue to the next staged phase.
- Project state docs summarize the second re-proof outcome.

Notes
- Keep the decision conservative.
- Do not use this task to justify multi-task widening unless the measured result is genuinely strong.
