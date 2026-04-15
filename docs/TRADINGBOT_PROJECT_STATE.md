# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state (post-Task 200)

- Tasks 157-200 are complete in bounded supervised scope.
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
  - a durable two-task canary scorecard and benchmark artifacts,
  - a real bounded two-task pilot runner exercised over a curated adjacent-pair corpus,
  - reliability benchmark artifacts and a regression matrix,
  - docs-status guarding,
  - explicit model-profile and transport declaration,
  - additive dual-transport support,
  - provider/model capability negotiation and fallback diagnostics,
  - a durable contract/model transport checkpoint,
  - raw-output capture integrity and explicit empty-output classification,
  - expanded transport-failure artifacts and parser-path observability,
  - protected-method preflight tracing and fallback discipline,
  - transport-health benchmarking and a recurring failure-family corpus,
  - a post-195 transport-stability checkpoint,
  - a post-transport one-task rebenchmark and empty-output regression guard,
  - a transport-stable bounded two-task scorecard refresh on the recovered runtime path,
  - adjacent-pair resume precision truth,
  - an explicit supervised three-step canary admission contract,
  - and a post-200 execution checkpoint that keeps widening bounded and supervision-aware.

## Honest current posture

- One-task lane: this is the strongest proven path. It is conditionally ready under supervision on the recovered runtime path, with explicit transport observability and an empty-output regression guard.
- Two-task lane (bounded pilot): this is the only real multi-task execution shape with durable operational proof today. It remains bounded, supervised, and curated.
- Three-step lane (canary chain): admitted and checkpoint-authorized only as a narrow supervised shape. The repo has the contract surface for A->B->C, but it does not yet have durable real-run proof that this should be treated as an operational multi-task path.
- Multi-agent role orchestration: controller / builder / verifier surfaces exist and are useful inside bounded flows, but they are not yet proven as a general role-routing system across arbitrary multi-task sequences.
- Post-200 checkpoint: conditionally ready under supervision to plan one more cautious widening slice. This still does not justify unattended multi-task autonomy, arbitrary scheduling, or standalone productization.

This means:

- one-task work remains the default proving path under light supervision,
- the bounded supervised two-task pilot remains the only justified operational multi-task form,
- a three-step canary may now be pursued only as an explicitly supervised proof path,
- transport behavior is materially more observable and diagnosable than before,
- broad unattended multi-task autonomy is still not justified,
- and the standalone orchestrator-app phase remains blocked behind stronger chained execution proof.

## What the repo is good at now

The repo is now good at:

- completing one task with a conservative supervised loop,
- recovering from some transport and bundle-shape failures that used to collapse runs early,
- preserving exact deliverable contracts and protected-surface discipline,
- measuring two-task bounded pilot behavior honestly,
- distinguishing direct progress from supervision-assisted progress in the bounded two-task lane,
- and persisting resume and checkpoint truth well enough to reason about adjacent re-entry.

## What still needs work

The repo still needs work on:

- converting the three-step canary from contract-only truth into real execution proof,
- making controller route decisions durable and resumable across chained runs,
- improving confidence that a small adjacent manifest can stop, resume, and fail honestly without broad human steering,
- keeping compatibility-surface regressions from leaking into widening tasks,
- and reducing reliance on protected-method or control-plane-sensitive edits during widening slices.

## What still blocks the next phase

Before broader autonomy or product extraction can be justified, the repo still needs:

- a real supervised three-step canary runner,
- a curated three-step canary corpus with explicit positive and negative cases,
- a benchmark and scorecard for three-step canary behavior that keeps supervision truth first-class,
- durable controller-route trace and resume reconstruction across chained canary runs,
- and a checkpoint that decides whether a tiny adjacent-manifest gate is justified under supervision.

## Active tranche

Current active tranche: 201-205.

## Immediate continuation target (Tasks 201-205)

Convert the admitted three-step canary surface into real supervised execution proof before attempting any broader multi-task gate:

- 201 — supervised three-step canary runner and durable chain ledger
- 202 — curated three-step canary corpus and manifest truth
- 203 — three-step canary benchmark and supervision-aware scorecard
- 204 — controller route trace and resume reconstruction for chained canary runs
- 205 — supervised multi-task canary checkpoint and adjacent-manifest gate

## Why this tranche exists

Tasks 196-200 finished the post-transport execution reproof tranche honestly. That checkpoint did not reopen broad autonomy. It only authorized a very narrow next step.

The next tranche therefore should not jump to arbitrary multi-task manifests. It should first prove the smallest newly admitted widening shape in real execution:

- exactly three adjacent tasks,
- explicitly supervised,
- controller-route and resume truth preserved,
- benchmarked,
- and still reversible if the evidence degrades.

## Task 201 update

A supervised three-step canary runner and durable chain ledger have been added:

- Runner: `agents/lib/three_step_canary.py`
- Ledger path format: `<artifacts_dir>/three_step_canary/<session_id>/chain_ledger.json`
- The ledger records: session id, task ids and order, adjacency truth for A->B and B->C, supervision truth, resume truth per adjacent pair, and terminal chain outcome.

A corresponding test verifies acceptance of exactly three adjacent tasks, conservative rejection of malformed shapes, and durable ledger persistence:
- `tests/test_three_step_canary.py`
