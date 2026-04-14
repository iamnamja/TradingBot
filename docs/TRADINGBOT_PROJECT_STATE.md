# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state (post-Task 180)

- Tasks 157–180 are complete in bounded supervised scope.
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
  - a bounded two-task pilot re-proof with explicit canary and corpus-backed promotion payloads.

## Honest current posture

- One-task lane: conditionally ready under supervision for benchmark-eligible work (default path).
- Two-task lane (bounded pilot): ready for a bounded supervised two-task pilot on the curated adjacent-pair corpus, governed by admission, handoff, and role-split truth and measured by conservative canary scorecards and corpus-backed `two_task/bounded_corpus` artifacts.

This means:

- one-task work remains the default proving path under light supervision,
- the two-task pilot can proceed in a bounded, supervised manner on the curated corpus,
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
    - `two_task/bounded_corpus/bounded_corpus_promotion.json` (durable widening checkpoint and conservative verdict)

Compatibility note: the canary and corpus benchmarks write only `canary_*` or `two_task/bounded_corpus/*` artifacts and never modify the strict one-task `scorecard.json`, `scoreboard.json`, or `promotion.json` files.

## Bounded two-task pilot re-proof (Tasks 175–180)

- Verdict: ready for a bounded supervised two-task pilot on the curated adjacent-pair corpus.
- Rationale: admission/handoff/role-split truth is explicit and measured; canary trials and real corpus runs produce durable artifacts; supervision remains required.
- Widening checkpoint: only cautiously widen the curated corpus while staying supervised and only when corpus metrics justify it. Broad unattended multi-task autonomy remains blocked. Standalone orchestrator productization remains blocked.
- Product checkpoint: the orchestrator continues to operate inside the monorepo with an explicit consumer bridge; the standalone app phase remains blocked pending broader multi-task autonomy proof.

## Immediate continuation target

Operate the bounded supervised two-task pilot and gather corpus evidence:

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

## Two-task pilot benchmark entrypoints and artifacts

- One-task strict scorecard session wiring remains unchanged and is the source of truth for the one-task lane.
- Two-task canary entry: `builder.orchestrator.benchmark.run_two_task_canary_benchmark(...)`
  - Artifacts: `canary_trials.json`, `canary_scorecard.json`, `canary_promotion.json`
- Two-task real bounded corpus entry: `builder.orchestrator.bounded_corpus_benchmark.run_bounded_two_task_corpus_benchmark(...)`
  - Artifacts: `two_task/bounded_corpus/pairs.json`, `two_task/bounded_corpus/summary.json`, `two_task/bounded_corpus/bounded_corpus_promotion.json`

The corpus promotion artifact records a conservative verdict and an explicit widening checkpoint with blocked areas enumerated.
