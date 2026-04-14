# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state (post-Task 185)

- Tasks 157–185 are complete in bounded supervised scope.
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
  - a real bounded two-task pilot runner exercised over a curated adjacent-pair corpus,
  - a bounded two-task pilot re-proof with explicit canary and corpus-backed promotion payloads,
  - import/public compatibility guardrails for orchestrator benchmark surfaces to prevent additive regressions (Task 182),
  - reliability benchmark artifacts and a regression matrix (Task 184),
  - a durable post-185 reliability checkpoint and explicit capability-resume gate (Task 185).

## Honest current posture

- One-task lane: conditionally ready under supervision for benchmark-eligible work (default path).
- Two-task lane (bounded pilot): ready for a bounded supervised two-task pilot on the curated adjacent-pair corpus, governed by admission, handoff, and role-split truth and measured by conservative canary scorecards and corpus-backed `two_task/bounded_corpus` artifacts.
- Reliability checkpoint (Task 185): conditionally ready under supervision to plan a cautious, bounded capability-widening slice. This does not unblock unattended multi-task autonomy or standalone productization.

This means:

- one-task work remains the default proving path under light supervision,
- the two-task pilot can proceed in a bounded, supervised manner on the curated corpus,
- any widening remains bounded and cautious, based on reliability evidence,
- broad multi-task autonomy is still not justified,
- and the standalone orchestrator-app phase remains blocked behind stronger multi-task autonomy proof.

## Separation of one-task truth and two-task pilot truth

- One-task benchmark and promotion artifacts remain the source of truth for the already-proven lane. They persist into:
  - `scorecard.json` (strict no-manual-intervention counts),
  - `scoreboard.json` (pass-rate compatibility surface),
  - `promotion.json` (promotion verdict for one-task lane).

- Two-task pilot artifacts are persisted alongside the one-task artifacts, without altering the one-task surfaces:
  - Canary pilot (entrypoint in the benchmark module):
    - `canary_trials.json`
    - `canary_scorecard.json`
    - `canary_promotion.json`
  - Real bounded corpus pilot (entrypoint `builder.orchestrator.bounded_corpus_benchmark.run_bounded_two_task_corpus_benchmark(...)`):
    - `two_task/bounded_corpus/pairs.json`
    - `two_task/bounded_corpus/summary.json`
    - `two_task/bounded_corpus/bounded_corpus_promotion.json`

Compatibility note: the canary and corpus benchmarks write only `canary_*` or `two_task/bounded_corpus/*` artifacts and never modify the strict one-task `scorecard.json`, `scoreboard.json`, or `promotion.json` files. Import/public contract guardrails now protect these entrypoints from accidental drift.

## Reliability-first continuation checkpoint (Tasks 181–185)

A reliability tranche has been completed with the following evaluation:

- recurring failure-family reduction: evaluated via best-effort deltas when previous reliability snapshots exist; otherwise treated conservatively,
- retry-count improvement: tracked explicitly in the reliability matrix,
- supervision/intervention rate: tracked by lane and normalized by run count,
- compatibility-regression reduction: tracked explicitly and normalized by run count,
- resume-safe recovery behavior: inferred from resume-related failure-family counts; ambiguous signals default to a safe restart posture.

Artifact paths:

- `reliability/one_task_reliability.json`
- `reliability/two_task_reliability.json`
- `reliability/reliability_matrix.json`
- `reliability/reliability_checkpoint.json` (Task 185)

## Capability-resume gate verdict (Task 185)

- Verdict: conditionally ready under supervision.
- Gate meaning: a cautious bounded next slice may be planned under supervision if reliability metrics remain within conservative thresholds. This is not blanket permission for broad autonomy.
- Blocked areas (remain explicit):
  - broad unattended multi-task autonomy,
  - standalone orchestrator productization.

## What still blocks the next phase

Before broad multi-task autonomy or product extraction can be justified, the repo still needs:

- sustained two-task corpus evidence from real bounded pilot runs across curated adjacent-task pairs,
- lower supervised-intervention rates on the bounded pilot lane,
- durable pair-level ledgers that distinguish autonomous progress from operator help,
- additional authority-corroboration truth and failure-family elimination for multi-task sequences beyond the first adjacent pair,
- sharper failure-family classification so repair selection lands on the correct surface more often,
- better resume-safe recovery so partially-successful runs re-enter from precise checkpoints instead of broad retries.

## Immediate continuation target (Tasks 186+)

Continue reliability-first improvements while operating within the cautious bounded scope:

- maintain and improve supervision-rate, retry-count, and compatibility-regression metrics,
- reduce resume/re-entry ambiguity and improve safe checkpointing,
- only expand pilot boundaries when reliability checkpoint evidence meets or exceeds conservative thresholds for both lanes.
