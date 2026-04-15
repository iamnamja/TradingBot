# Orchestrator Post-Transport Execution Reproof Guide (196-200)

## Goal of this tranche

The goal is to prove that the recovered runtime path holds up under real execution, not just under transport-focused diagnostics.

## Why this tranche exists

The 191-195 tranche made transport failures observable and materially reduced the empty-output black-box problem.

That recovery is necessary, but it is not enough to widen claims. The runner still needs fresh one-task and bounded two-task execution proof on the recovered path before any cautious widening step is honest.

## What this tranche should accomplish

### One-task reproof
- refresh one-task benchmark evidence on the recovered runtime path
- add a regression guard so empty-output failures do not quietly re-enter the one-task lane

### Bounded two-task reproof
- rerun bounded two-task pilot evidence on the recovered runtime path
- refresh scorecards and promotion payloads conservatively

### Resume precision
- tighten adjacent-pair checkpoint and resume truth
- distinguish precise re-entry from broad rerun behavior

### Smallest widening step only
- if and only if earlier tasks stay stable, define a supervised three-step canary contract
- keep admission, supervision, and benchmark truth explicit

### Final checkpoint
- record whether the repo is ready to plan a bounded next slice
- keep the verdict conservative and supervision-aware

## Operator guidance

- continue using `gpt-5` as the known-good baseline unless a task explicitly proves another path
- prefer narrow benchmark, checkpoint, and resume-safety changes
- keep runtime/debug artifacts ignored and out of branch diffs
- treat any regression back toward empty-output capture as a stop signal, not a minor warning
- do not widen claims faster than the checkpoint artifacts justify
