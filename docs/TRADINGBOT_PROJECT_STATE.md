# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state (post-Task 175)

- Tasks 157–175 are complete in bounded supervised scope.
- The repo now has:
  - a strict no-manual-intervention one-task scorecard,
  - deliverable-contract and completion-integrity enforcement,
  - authority corroboration and conservative run truth,
  - narrowed top one-task failure-family handling,
  - a durable one-task promotion verdict,
  - an explicit default one-task path,
  - a conservative two-task pilot admission gate,
  - a bounded adjacent-task A->B handoff contract,
  - a supervised builder/verifier role split scoped for the pilot,
  - a durable two-task canary scorecard and benchmark artifacts integrated into the existing benchmark session directory,
  - and a bounded two-task pilot re-proof with an explicit canary promotion payload.

## Honest current posture

- One-task lane: conditionally ready under supervision for benchmark-eligible work (default path).
- Two-task lane (bounded pilot): ready for a bounded supervised two-task pilot, governed by admission, handoff, and role-split truth and measured by conservative canary scorecards and `canary_promotion.json`.

This means:

- one-task work remains the default proving path under light supervision,
- the two-task pilot can proceed in a bounded, supervised manner,
- broad multi-task autonomy is still not justified,
- and the standalone orchestrator-app phase remains blocked behind stronger multi-task autonomy proof.

## Separation of one-task truth and two-task canary truth

- One-task benchmark and promotion artifacts remain the source of truth for the already-proven lane. They persist into:
  - `scorecard.json` (strict no-manual-intervention counts),
  - `scoreboard.json` (pass-rate compatibility surface),
  - `promotion.json` (promotion verdict for one-task lane).

- Two-task canary pilot artifacts are persisted alongside the one-task artifacts, without altering the one-task surfaces:
  - `canary_trials.json` (per-attempt durable truth),
  - `canary_scorecard.json` (pilot attempts, completions, blocked admissions, ineligible attempts, handoff-incomplete/incompatible failures, supervised interventions),
  - `canary_promotion.json` (bounded-pilot readiness verdict and thresholds).

Compatibility note: the canary benchmark writes only `canary_*` artifacts and never modifies the strict one-task `scorecard.json`, `scoreboard.json`, or `promotion.json` files.

## Bounded two-task pilot re-proof (Task 175)

- Verdict: ready for a bounded supervised two-task pilot.
- Rationale: admission/handoff/role-split truth is explicit and measured; initial canary trials and scorecards are durable and conservative; supervision remains required.
- Product checkpoint: the orchestrator continues to operate inside the monorepo with an explicit consumer bridge; the standalone app phase remains blocked pending broader multi-task autonomy proof.

## Immediate continuation target

The next active work is not broad widening. It is bounded supervised two-task pilot operation and evidence gathering through Tasks 176–180:

- 176 — bounded two-task pilot runner and pair ledger
- 177 — curated adjacent-pair corpus and admission manifest
- 178 — supervised intervention artifact and pilot failure digest
- 179 — real bounded two-task corpus benchmark
- 180 — bounded two-task corpus re-proof and widening checkpoint

## What still blocks the next phase

Before broad multi-task autonomy or product extraction can be justified, the repo still needs:

- sustained two-task corpus evidence from real bounded pilot runs across curated adjacent-task pairs,
- lower supervised-intervention rates on the bounded pilot lane,
- durable pair-level ledgers that distinguish autonomous progress from operator help,
- additional authority-corroboration truth and failure-family elimination for multi-task sequences beyond the first adjacent pair.

## Operator workflow for the current tranche

Use the current tranche conservatively:

- review merged-main snapshots first,
- plan narrowly from the uploaded source-of-truth files,
- patch docs/tasks/code only as needed,
- validate on a clean branch,
- inspect diffs before merge,
- and preserve branch and runtime-artifact hygiene.

Operational reference: `docs/ORCHESTRATOR_BOUNDED_TWO_TASK_PILOT_OPERATIONS.md`

## Two-task canary benchmark entrypoint and artifacts

- Entry: `builder.orchestrator.benchmark.run_two_task_canary_benchmark(...)`
- Artifacts (persisted under the same session directory used by one-task benchmarks):
  - `canary_trials.json`
  - `canary_scorecard.json`
  - `canary_promotion.json`

The canary scorecard captures explicit ineligibility and admission-blocked attempts so that pilot gating and widening decisions are based on explicit, durable truth rather than intuition.
