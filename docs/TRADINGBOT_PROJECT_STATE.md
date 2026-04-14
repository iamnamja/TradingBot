# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state (post-Task 184)

- Tasks 157–182 are complete in bounded supervised scope.
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
  - import/public compatibility guardrails for orchestrator benchmark surfaces to prevent additive regressions (Task 182).

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
    - `two_task/bounded_corpus/bounded_corpus_promotion.json`

Compatibility note: the canary and corpus benchmarks write only `canary_*` or `two_task/bounded_corpus/*` artifacts and never modify the strict one-task `scorecard.json`, `scoreboard.json`, or `promotion.json` files. Import/public contract guardrails now protect these entrypoints from accidental drift.

## Reliability-first continuation checkpoint (post-Task 180)

The project is now at the right point to prioritize runtime reliability over immediate capability widening.

Why this is the next step:

- the repo now has bounded one-task and two-task proof surfaces, so the next bottleneck is less about inventing new pilot artifacts and more about reducing recurring orchestration failures,
- recent work showed that benchmark compatibility, import/public contract drift, and exact proof-task admission rules can still derail otherwise-reasonable tasks,
- the next tranche should therefore harden runtime classification, compatibility guardrails, and resume/re-entry paths before any new role-routing or deeper task-chain claims are attempted.

## What still blocks the next phase

Before broad multi-task autonomy or product extraction can be justified, the repo still needs:

- sustained two-task corpus evidence from real bounded pilot runs across curated adjacent-task pairs,
- lower supervised-intervention rates on the bounded pilot lane,
- durable pair-level ledgers that distinguish autonomous progress from operator help,
- additional authority-corroboration truth and failure-family elimination for multi-task sequences beyond the first adjacent pair,
- sharper failure-family classification so repair selection lands on the correct surface more often,
- better resume-safe recovery so partially-successful runs re-enter from precise checkpoints instead of broad retries.

## Immediate continuation target (Tasks 181–185)

Operate a reliability-first tranche before any capability widening:

- 181 — classify recurring failure families and choose narrower repair targets
- 182 — harden import/public benchmark compatibility contracts and additive-surface guarantees (with cross-platform artifact path checks)
- 183 — persist resume-safe attempt checkpoints and recovery re-entry truth
- 184 — benchmark one-task and bounded two-task reliability by failure family, retry count, and supervision rate
- 185 — record a reliability checkpoint and explicit gate for when capability widening may resume

## Operator workflow for the next tranche

Use the next tranche conservatively:

- review merged-main snapshots first,
- plan narrowly from the uploaded source-of-truth files,
- patch docs/tasks/code only as needed,
- validate on a clean branch,
- inspect diffs before merge,
- preserve branch and runtime-artifact hygiene,
- and keep any reliability instrumentation additive to the existing one-task and two-task truth surfaces.

Operational reference: `docs/ORCHESTRATOR_RELIABILITY_FIRST_181_185.md`

## Reliability-first addition (Task 181)

Task 181 adds a durable failure-family taxonomy and conservative repair-target selection:

- Implementation: agents/lib/repair_targeting.py (classification, short codes, target selection, persistence)
- Tests: tests/test_repair_targeting.py
- Behavior: narrows default repair surfaces per family, reduces broad fallback repairs, preserves protected and one-task proof surfaces.

These helpers are additive and can be reused by the existing repair planner without broader orchestrator rewrites.

## Reliability-first addition (Task 182)

Task 182 adds explicit import/public compatibility guardrails across benchmark entrypoints:

- One-task strict scorecard wiring is part of the public surface and is enforced by tests.
- Two-task canary artifacts are isolated behind `canary_*` and never touch one-task artifacts.
- Bounded-corpus benchmark writes exclusively to `two_task/bounded_corpus/` and emits a conservative promotion/checkpoint artifact.
- Tests ensure import stability and OS-agnostic artifact path discipline.
- Compatibility aliases and explicit module exports prevent accidental import-surface regression.

## Reliability-first addition (Task 183)

Task 183 adds explicit attempt-state persistence and resume-safe checkpoints:

- Implementation: agents/lib/resume_state.py (serialized checkpoint objects), agents/lib/attempt_state.py (persistence and re-entry planner)
- Tests: tests/test_attempt_state_resume.py
- Behavior: distinguishes fresh execution, retry-after-failure, resume-after-partial, and manual-intervention; records last safe transition and intended surface; chooses conservative restart if state is ambiguous or unsafe.

## Reliability-first addition (Task 184)

Task 184 adds a dedicated reliability benchmark and regression matrix:

- Code: src/builder/orchestrator/reliability_benchmark.py
- Artifacts (additive, separate from promotion):
  - reliability/one_task_reliability.json
  - reliability/two_task_reliability.json
  - reliability/reliability_matrix.json
- Metrics: run count, aggregate retries to green, failure-family counts, supervision rate, admission-block frequency, and compatibility-regression frequency.
- Tests: tests/test_reliability_benchmark.py

This reliability view is additive and never overwrites strict one-task or two-task canary/corpus artifacts.
