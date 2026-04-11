# Task 166 — orchestrator strict no-manual-intervention scorecard

## Why

After the second one-task reliability re-proof, we still need a benchmark truth model that makes it impossible to over-credit runs that only succeeded because a human stepped in mid-run. The scorecard must reflect autonomous reality, not salvaged outcomes.

## Scope

Extend the benchmark/session artifacts so promotion and widening decisions are based on a strict no-manual-intervention scorecard.

## Requirements

- Add or update scorecard fields that clearly separate:
  - total benchmark runs,
  - direct completions,
  - self-healed completions,
  - failed runs,
  - supervised or escalated runs,
  - authority-blocked runs,
  - runs invalidated by human intervention.
- Any human code or content edit during a benchmark run must invalidate autonomous success for that run.
- Keep compatibility with existing benchmark/session artifacts rather than creating a disconnected parallel reporting lane.
- Persist a durable scorecard artifact suitable for comparing benchmark sessions over time.

## Create or update these exact files
- src/builder/orchestrator/benchmark.py
- src/builder/orchestrator/benchmark_scorecard.py
- tests/test_benchmark_scorecard_integration.py
- tasks/166_orchestrator_strict_no_manual_intervention_scorecard.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove that a manual edit during a benchmark run prevents the run from being counted as an autonomous success.
- Tests prove that direct completions and self-healed completions are still tracked separately.
- Docs explain that promotion and widening decisions use this stricter scorecard rather than ad hoc observations.

## Implementation notes

- The strict scorecard is persisted to scorecard.json in each benchmark session directory alongside a legacy-compatible scoreboard.json.
- Any manual edit flips a run into the "invalidated_by_human_intervention" bucket and removes it from autonomous success counts, even if execution otherwise succeeded.
- The benchmark harness wires the strict scorecard writer directly into session persistence to keep artifacts cohesive and durable.
