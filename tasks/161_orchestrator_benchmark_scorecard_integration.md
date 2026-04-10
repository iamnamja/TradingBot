# Task 161 — orchestrator benchmark scorecard integration

## Goal
Wire the strict no-manual-intervention scorecard into the existing one-task benchmark/session artifact flow so Task 157 stops being a standalone helper and becomes a real benchmark proof surface.

## Why
The first autonomous attempt at Task 157 showed that the orchestrator can create a local scorecard helper and tests, but still miss the actual integration points that make the task operationally meaningful.

## Requirements
- Integrate the strict scorecard into the existing benchmark/session artifact path introduced by Task 156.
- Extend current benchmark outputs instead of creating a disconnected side helper.
- Preserve compatibility with the existing pass-rate scoreboard and failure-digest surfaces.
- Treat any human mid-run intervention as disqualifying autonomous success for the affected run.
- Keep the implementation narrow and benchmark-lane only.

## Acceptance
- Benchmark/session artifacts include strict no-manual-intervention fields or a dedicated strict scorecard artifact.
- Existing benchmark tests still pass.
- New tests prove that manual intervention invalidates autonomous promotion even if checks are green.
- State/docs reflect that promotion decisions use the stricter benchmark scorecard.
