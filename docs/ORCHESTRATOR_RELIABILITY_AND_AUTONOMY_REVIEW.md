# Orchestrator Reliability / Recovery / Autonomy Review

## Why this review exists

The orchestrator has moved beyond pure hardening and into a bounded one-task autonomous lane. The next question is no longer “can it route a task safely?” The next question is “can it complete ordinary one-task work reliably enough that operators stop patching it by hand?”

## Current strengths

- shell-routed execution and worktree/branch guardrails are present
- protected-file policies exist
- validator and failure-journal seams exist
- hosted-authority interpretation around `ci-required` is explicit
- the repo now has a bounded one-task autonomous lane with ledger, canary reporting, supervised handoff, resume state, operator proof bundle, a deterministic developer / verifier / repair / controller execution record, and an external-safe failure taxonomy that chooses narrower self-heal lanes for ordinary failures
- the scheduler can route exactly one admitted safe task through the canonical bounded runner

## Current weakness that matters most now

The project still does too much **manual recovery** for ordinary one-task work.

That means the next phase should not prioritize a broader autonomy surface. It should prioritize execution quality and self-heal quality on a clean external-safe corpus.

## The current bottleneck

The main bottleneck is now:

- can the bounded lane finish ordinary safe implementation tasks
- can it diagnose common failures without operator editing
- can it apply the smallest credible repair
- can it show a real pass rate instead of anecdotal success stories

## Agreed phase order

1. make one-task autonomous execution actually work on ordinary external-safe tasks
2. only then widen carefully into bounded multi-task execution
3. only after that package the orchestrator as its own operator-facing app
4. self-hosting app work is a later privilege, not the current proving ground

## Immediate build priorities

1. external-safe task corpus and evaluation manifest
2. one-task multi-agent dev / test / repair / controller loop with explicit role-produced evidence
3. external-safe failure taxonomy and self-heal router
4. pass-rate scoreboard and failure digest
5. external-safe corpus reliability re-proof
6. two-task readiness gate and phase transition

Task 151 sharpens the current one-task lane by teaching it to distinguish common external-safe failure families instead of relying on a generic retry posture. That means ordinary import/collection failures, lint-only failures, missing deliverable coverage, missing required file updates, and focused test regressions can now route to a smaller credible repair path before the lane escalates.

## Desired outcome of the next tranche

By the end of the next tranche, the project should be able to answer:

- what the bounded one-task lane’s real external-safe pass rate is
- which failure classes dominate manual intervention
- whether targeted self-heal materially improves completion
- whether the project has earned the right to start bounded two-task trials
