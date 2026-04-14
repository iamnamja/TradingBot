# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state (post-Task 172)

- Tasks 157–172 are complete in bounded supervised scope.
- The repo now has:
  - a strict no-manual-intervention one-task scorecard,
  - deliverable-contract and completion-integrity enforcement,
  - authority corroboration and conservative run truth,
  - narrowed top one-task failure-family handling,
  - a durable one-task promotion verdict,
  - an explicit default one-task path,
  - a conservative two-task pilot admission gate,
  - and a bounded adjacent-task A->B handoff contract.

## Honest current posture

The one-task lane is conditionally ready under supervision for benchmark-eligible work.

That means:

- one-task work can now be treated as the default proving path for eligible tasks under light supervision,
- bounded two-task pilot preparation is underway,
- but broad multi-task autonomy is still not justified,
- and the standalone orchestrator-app phase remains blocked behind bounded two-task pilot proof.

## What still blocks the next phase

Before a bounded two-task pilot can be justified, the repo still needs:

- explicit supervised builder/verifier role separation for pilot work,
- a durable two-task canary scorecard,
- and a bounded pilot re-proof.

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
