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
  - a documented default-path plus explicit future two-task pilot gate,
  - a mechanical two-task pilot admission truth surface,
  - and an additive adjacent-task A->B handoff contract.

## Honest current posture

The one-task lane is conditionally ready under supervision for benchmark-eligible work.

That means:

- one-task work can now be treated as the default proving path for eligible tasks under light supervision,
- bounded two-task pilot preparation is underway,
- but widening beyond the bounded supervised pilot still requires explicit proof,
- and the standalone orchestrator-app phase remains blocked behind bounded multi-task proof.

## What still blocks the next phase

Before a bounded two-task pilot can be justified, the repo still needs:

- explicit supervised dev/test role separation for pilot work,
- a durable two-task canary scorecard,
- and a bounded pilot re-proof.

## Next continuation direction

The next tranche should focus on bounded two-task pilot preparation under supervision, not on broad widening.

## Task 173 execution discipline update

Fresh reruns showed a repeat failure family for Task 173: making the dev/test split explicit is the correct next seam, but the implementation keeps drifting into replacements of frozen controller-contract and single-task reporting surfaces.

So Task 173 should now be treated explicitly as an extension-only change:

- preserve frozen/public surfaces in `agents.lib.multi_agent_contract`,
- preserve existing single-task reporting and proof helpers in `agents.run_single_task`,
- preserve existing compatibility behavior in `agents.lib.multi_agent_loop`,
- and add the supervised builder/verifier split only as a bounded additive seam.

This keeps the task aligned with the honest project posture: bounded two-task pilot preparation under supervision, not broad refactoring or widening.

## Task 173 supervised dev/test role split for bounded pilot

This task makes the pilot’s dev/test split explicit without inventing new role types:

- “dev” is treated as the existing builder role and “test” as the existing verifier role.
- Controller remains the sole authority to approve the next transition; specialist-to-specialist hops do not bypass the controller gate.
- The pilot role sequence is explicit, inspectable, and bounded to the supervised lane. Supported sequences are:
  - builder → verifier → controller
  - verifier → builder → controller
- The runtime stops conservatively when an unsupported sequence is requested or when controller authority would be bypassed.
- This change does not claim general autonomous multi-agent execution; it is a supervised, bounded pilot-only split reused through the existing builder/verifier/controller model.
- Any new checkpoint or artifact must append fields rather than replacing existing single-task or controller-contract surfaces.
