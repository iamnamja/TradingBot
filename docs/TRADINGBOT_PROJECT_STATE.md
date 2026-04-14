# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state (post-Task 174)

- Tasks 157–174 are complete in bounded supervised scope.
- The repo now has:
  - a strict no-manual-intervention one-task scorecard,
  - deliverable-contract and completion-integrity enforcement,
  - authority corroboration and conservative run truth,
  - narrowed top one-task failure-family handling,
  - a durable one-task promotion verdict,
  - an explicit default one-task path,
  - a conservative two-task pilot admission gate,
  - a bounded adjacent-task A->B handoff contract,
  - and a durable two-task canary scorecard and benchmark artifacts integrated into the existing benchmark session directory.

## Honest current posture

The one-task lane is conditionally ready under supervision for benchmark-eligible work.

That means:

- one-task work can now be treated as the default proving path for eligible tasks under light supervision,
- bounded two-task pilot preparation is underway,
- but broad multi-task autonomy is still not justified,
- and the standalone orchestrator-app phase remains blocked behind bounded two-task pilot proof.

## Separation of one-task truth and two-task canary truth

- One-task benchmark and promotion artifacts remain the source of truth for the already-proven lane. They persist into:
  - `scorecard.json` (strict no-manual-intervention counts),
  - `scoreboard.json` (pass-rate compatibility surface),
  - `promotion.json` (promotion verdict for one-task lane).

- Two-task canary pilot artifacts are now persisted alongside the one-task artifacts, without altering the one-task surfaces:
  - `canary_scorecard.json` (pilot attempts, completions, blocked admissions, ineligible attempts, handoff-incomplete/incompatible failures, supervised interventions),
  - `canary_promotion.json` (bounded-pilot readiness verdict and thresholds),
  - `canary_trials.json` (durable per-attempt records for later analysis and reproof of thresholds).

This keeps the proven one-task lane unchanged while enabling honest supervised evaluation for the bounded two-task pilot.

Compatibility note: the canary benchmark writes only `canary_*` artifacts and never modifies the strict one-task `scorecard.json`, `scoreboard.json`, or `promotion.json` files.

## What still blocks the next phase

Before a bounded two-task pilot can be justified broadly, the repo still needs:

- explicit supervised builder/verifier role separation for pilot work,
- a durable two-task canary scorecard (added in Task 174),
- a bounded pilot re-proof (targeted in Task 175).

## Task 173 execution discipline update

Fresh reruns showed that the original single Task 173 was still too broad.

The intended pilot behavior was valid:
- map pilot `dev` to `builder`
- map pilot `test` to `verifier`
- keep `controller` as the only approval authority
- keep the pilot bounded and supervised

But the single task kept mixing two jobs:
- preserving/restoring the shared controller-contract compatibility surface
- adding the bounded pilot role-sequence behavior

Those jobs are now split:

- `173a`: controller-contract compatibility for bounded pilot
- `173b`: supervised dev/test role split for bounded pilot

This keeps the work aligned with the repo's honest posture: additive bounded pilot preparation under supervision, not broad contract refactoring.

## Two-task canary benchmark entrypoint and artifacts

- Entry: `builder.orchestrator.benchmark.run_two_task_canary_benchmark(...)`
- Artifacts (persisted under the same session directory used by one-task benchmarks):
  - `canary_trials.json`
  - `canary_scorecard.json`
  - `canary_promotion.json`

The canary scorecard captures explicit ineligibility and admission-blocked attempts so that pilot gating and widening decisions are based on explicit, durable truth rather than intuition.
