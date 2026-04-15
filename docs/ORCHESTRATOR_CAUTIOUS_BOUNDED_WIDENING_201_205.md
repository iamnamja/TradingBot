# Orchestrator Cautious Bounded Widening Guide (201-205)

## Goal of this tranche

The goal of this tranche is to turn the newly admitted three-step canary shape into real supervised execution proof.

## Why this tranche exists

The post-200 checkpoint established that the repo may plan one more bounded widening slice under supervision.

That permission is narrow. It does not authorize arbitrary multi-task manifests, unattended autonomy, or broad controller-led scheduling.

## What this tranche should accomplish

### Real three-step canary execution
- add an exactly-three-task adjacent canary runner
- persist a durable chain ledger that preserves admission, handoff, supervision, and terminal truth

### Durable canary corpus
- define a curated three-step canary corpus
- keep positive, negative, and supervision-heavy cases explicit

### Benchmark and scorecard truth
- benchmark the three-step canary path separately from one-task and bounded two-task truth surfaces
- keep direct progress vs supervision-assisted progress explicit
- make chain-break categories and manual intervention observable

### Controller-route truth
- persist the controller’s route choices and why it selected builder, verifier, stop, or manual escalation across the canary chain
- make interrupted canary runs resumable without losing pending-role truth

### Final checkpoint
- decide whether the repo is justified to admit a tiny adjacent manifest under supervision
- keep the verdict conservative and reversible

## Operator guidance

- continue using `gpt-5` as the known-good baseline unless a task explicitly proves another path
- prefer additive modules over broad rewrites to `agents/run_task.py`
- keep runtime/debug artifacts ignored and out of branch diffs
- treat compatibility-surface regressions as a stop signal for widening tasks
- preserve one-task and bounded two-task scorecard semantics while adding three-step canary truth additively
- do not widen claims faster than the checkpoint artifacts justify

## Scope honesty reminder

This tranche is still not about arbitrary scheduling. It is about one carefully bounded step:

- from one-task proof,
- through bounded two-task proof,
- into a supervised three-step canary proof,
- and only then, if the evidence is strong enough, into a tiny adjacent-manifest gate.
