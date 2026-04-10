# Task 157 — orchestrator strict no-manual-intervention scorecard

## Why

We need a scorecard that reflects real autonomous behavior, not salvaged outcomes after a human steps in. Without a strict scoring rule, the orchestrator can appear healthier than it really is.

## Scope

Extend the benchmark artifacts and scoreboarding so that autonomous benchmark results are graded under a strict no-manual-intervention rule.

## Requirements

- Add scorecard fields that clearly separate:
  - total benchmark runs,
  - direct completions,
  - self-healed completions,
  - failed runs,
  - supervised/escalated runs,
  - authority-blocked runs,
  - runs invalidated by human intervention.
- Any human code/content edit during a benchmark run must invalidate autonomous success for that run.
- Add a durable scorecard artifact suitable for comparing benchmark sessions over time.
- Keep compatibility with the existing pass-rate scoreboard and failure digest surfaces.

## Acceptance criteria

- Tests prove that a manual edit during a benchmark run prevents the run from being counted as an autonomous success.
- Tests prove that direct completions and self-healed completions are still tracked separately.
- Docs explain that benchmark promotion decisions are based on this stricter scorecard rather than ad hoc observations.
