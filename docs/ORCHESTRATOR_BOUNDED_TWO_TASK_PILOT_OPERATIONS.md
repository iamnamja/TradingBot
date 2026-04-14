# Orchestrator Bounded Two-Task Pilot Operations

## Purpose

This document is the operator-facing continuation guide for the bounded supervised two-task pilot tranche (Tasks 176–180).

It does not redefine the project direction. It records how to operate this tranche conservatively and how to judge success honestly.

## Current truth before Task 176

The repo is complete through Task 175.

The repo can honestly claim:

- the one-task lane is conditionally ready under supervision,
- the bounded supervised two-task pilot is ready to be exercised in bounded scope,
- and the standalone orchestrator-as-its-own-app phase remains blocked.

The repo cannot honestly claim:

- broad multi-task autonomy,
- unattended arbitrary task chaining,
- or standalone product readiness.

## Active tranche

The current execution order is:

1. `tasks/176_orchestrator_bounded_two_task_pilot_runner_and_pair_ledger.md`
2. `tasks/177_orchestrator_curated_adjacent_pair_corpus_and_admission_manifest.md`
3. `tasks/178_orchestrator_supervised_intervention_artifact_and_pilot_failure_digest.md`
4. `tasks/179_orchestrator_real_bounded_two_task_corpus_benchmark.md`
5. `tasks/180_orchestrator_bounded_two_task_corpus_reproof_and_widening_checkpoint.md`

## Operator rules for this tranche

- Review uploaded current-main snapshots before planning further work.
- Keep scope at exactly two tasks per bounded pilot run.
- Prefer narrow fixes when runtime or policy surfaces are the blocker.
- Reuse existing admission, handoff, role-split, and benchmark surfaces before adding anything new.
- Treat supervision as first-class truth. Human help must never be counted as autonomous success.
- Keep one-task benchmark and promotion surfaces unchanged.
- Do not widen into broad multi-task autonomy or standalone product claims in this tranche.

## Expected runtime posture

The bounded pilot should stay conservative.

It should stop or refuse to proceed when:

- fewer than two tasks are supplied,
- more than two tasks are supplied,
- the pair is not explicitly adjacent and handoff-eligible,
- admission truth blocks the pair,
- or the A->B handoff is incomplete or incompatible.

## Artifact expectations for Tasks 176–180

The tranche should produce durable bounded-pilot evidence, including:

- pair/session ledgers,
- curated pair manifests,
- supervised-intervention truth,
- bounded pilot failure digests,
- real corpus benchmark artifacts,
- and a conservative widening checkpoint.

Those artifacts should remain clearly separated from the already-proven one-task truth surfaces:

- `scorecard.json`
- `scoreboard.json`
- `promotion.json`

## Standard working cadence

The working cadence remains:

1. review current-main snapshots
2. produce a narrow patch zip
3. apply the patch on a clean branch
4. validate
5. inspect the diff
6. merge when honest
7. reset back to clean `main`
8. run the next numbered task

## Standard task run command

Use the numbered-task command in this form:

`py -m agents.run_task <task-file> --push --keep-runtime-artifacts --provider openai --model gpt-5`

## Branch and artifact hygiene

- Be strict about branch cleanliness.
- Do not ship runtime scratch or accidental local artifacts.
- If `_last_subset_preservation.json` appears in a branch diff, restore it from `origin/main` so it drops out of the diff.
- Keep fixes narrow when a task only partially completes.
- Do not overclaim success when the runtime evidence is partial.

## What success looks like at the end of Task 180

By the end of this tranche, the repo should have real bounded-pilot evidence strong enough to answer a narrow question honestly:

Should the project continue the bounded supervised two-task pilot as-is, widen the curated pair corpus cautiously while staying supervised, or remain blocked from any broader step?

That is the decision point. It is not permission to claim broad autonomy.
