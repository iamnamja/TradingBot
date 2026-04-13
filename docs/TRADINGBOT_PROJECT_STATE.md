# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state (post-Task 170)

- Tasks 157–170 are complete in bounded supervised scope.
- The repo now has:
  - a strict no-manual-intervention one-task scorecard,
  - deliverable-contract and completion-integrity enforcement,
  - authority corroboration and conservative run truth,
  - narrowed top one-task failure-family handling,
  - a durable one-task promotion verdict,
  - and a documented default-path plus explicit future two-task pilot gate.

## Honest current posture

The one-task lane is **conditionally ready under supervision** for benchmark-eligible work.

That means:

- one-task work can now be treated as the default proving path for eligible tasks under light supervision,
- but widening to a bounded two-task pilot still requires explicit proof,
- and the standalone orchestrator-app phase remains blocked behind bounded multi-task proof.

## What is now true after Task 170

- The repo has an explicit concept of a future bounded two-task pilot gate.
- The default one-task path and the future pilot path are documented separately.
- The project has not claimed broad multi-task autonomy.

## What still blocks the next phase

Before a bounded two-task pilot can be justified, the repo still needs:

- a mechanical pilot-admission truth surface,
- a deterministic adjacent-task handoff contract,
- explicit supervised dev/test role separation for pilot work,
- a durable two-task canary scorecard,
- and a bounded pilot re-proof.

## Next continuation direction

The next tranche should focus on bounded two-task pilot preparation under supervision, not on broad widening.


## Task 172 execution discipline update

Fresh reruns showed a repeat failure family for Task 172: adjacent-handoff logic is a valid next seam, but the implementation must preserve the repo's frozen multi-agent/public surfaces while adding the new bounded A->B handoff behavior.

So Task 172 should now be treated explicitly as an **extension-only** change:
- preserve frozen/public surfaces in `agents.lib.multi_agent_contract`,
- preserve existing single-task reporting/proof helpers in `agents.run_single_task`,
- preserve existing queue/controller behavior in `agents.lib.task_queue`,
- and add adjacent-task handoff truth only as a bounded additive seam.

This keeps the task aligned with the honest project posture: bounded two-task pilot preparation under supervision, not broad refactoring or widening.
