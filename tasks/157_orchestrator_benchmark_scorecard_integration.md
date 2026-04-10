# Task 157 — orchestrator benchmark scorecard integration

## Why

The first live proof-mode runs showed that a standalone scorecard helper is not enough. We need the strict scorecard rules wired into the benchmark/session path itself so autonomous results are measured from the same artifacts the orchestrator already emits.

## Scope

Integrate strict no-manual-intervention scorecarding into the existing benchmark/session artifact flow created by Task 156.

## Requirements

- Reuse the existing benchmark harness and session artifact path rather than creating a parallel reporting surface.
- Extend benchmark/session outputs so they record:
  - total benchmark runs,
  - direct completions,
  - self-healed completions,
  - failed runs,
  - authority-blocked runs,
  - supervised/escalated runs,
  - runs invalidated by human intervention.
- Preserve compatibility with the existing pass-rate scoreboard and failure-digest surfaces.
- Persist a durable scorecard artifact for each benchmark session.
- Update project docs to say that promotion decisions use the stricter integrated scorecard, not ad hoc interpretation.

## Acceptance criteria

- Tests prove that a manual edit during a benchmark run prevents that run from being counted as an autonomous success.
- Tests prove that direct completions and self-healed completions are still counted separately.
- Tests prove that the integrated session/scorecard artifact is written through the benchmark path.
- Docs/state files describe this scorecard as the basis for one-task promotion decisions.

## Notes

This task intentionally replaces the earlier standalone helper-only interpretation of Task 157. The goal is integration, not just local utility code.
