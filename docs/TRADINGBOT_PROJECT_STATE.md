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

The one-task lane is conditionally ready under supervision for benchmark-eligible work.

That means:

- one-task work can now be treated as the default proving path for eligible tasks under light supervision,
- but widening to a bounded two-task pilot still requires explicit proof,
- and the standalone orchestrator-app phase remains blocked behind bounded multi-task proof.

## What is now true after Task 170

- The repo has an explicit concept of a future bounded two-task pilot gate.
- The default one-task path and the future pilot path are documented separately.
- The project has not claimed broad multi-task autonomy.

## Runtime seams now shaping the next phase

- The existing Task 170 gate already lives in `agents.lib.task_queue`; the next task should refine that gate rather than invent a new pilot controller.
- The runtime already exposes adjacent-task truth through `depends_on`, `next_task_may_proceed`, and supervised handoff artifacts.
- The runtime already exposes explicit `controller` / `builder` / `verifier` role surfaces for bounded supervised work.
- The benchmark and promotion surfaces already exist in `src/builder/orchestrator/benchmark.py` and `benchmark_scorecard.py`.

## What still blocks the next phase

Before a bounded two-task pilot can be justified, the repo still needs:

- a mechanical pilot-admission truth surface,
- a deterministic adjacent-task handoff contract,
- explicit supervised builder/verifier role separation for pilot work,
- a durable two-task canary scorecard,
- and a bounded pilot re-proof.

## Next continuation direction

The next tranche should focus on bounded two-task pilot preparation under supervision, not on broad widening.

## Task 171 status: mechanical pilot admission and eligibility truth

- Two-task pilot admission is now mechanical and conservative, not subjective.
- The runtime extends the Task 170 gate to evaluate a structured promotion/admission payload (reusing the one-task promotion artifact produced by the strict scorecard).
- Eligibility reuses one-task promotion truth:
  - promotion verdict,
  - supervised or escalation rate,
  - unresolved authority-ambiguity rate,
  - and compatibility-regression state.
- The explicit operator flag and a hard cap of 2 tasks remain in force.
- When ineligible, explicit threshold reasons are returned, and an eligibility artifact is produced for durable, serializable comparison with future canary benchmark results.
