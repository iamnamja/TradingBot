# Orchestrator Roadmap 156–160

## Theme

Switch from feature-building mode to proof mode.

The repo now has a bounded one-task engine with multi-agent role separation, failure taxonomy, pass-rate/failure-digest artifacts, a truthful two-task readiness gate, and a bounded lint-only preflight. The next roadmap slice should stop primarily adding new orchestration surfaces and instead force the orchestrator to run real benchmark-eligible one-task work under a strict scorecard.

## Why this slice exists

The central risk now is not “missing one more elegant subsystem.” It is that we still know more about how to patch the orchestrator than how the orchestrator performs when it is the thing actually doing the work.

This slice addresses that by making orchestrator-run one-task benchmark trials the primary proving mode.

## Tasks

### 156 — one-task autonomous benchmark harness

Create a stable harness for running curated external-safe one-task trials through the existing bounded runner and persisting benchmark session artifacts.

### 157 — strict no-manual-intervention scorecard

Grade benchmark runs under a rule where any human mid-run intervention invalidates autonomous success for that run.

### 158 — authority corroboration and run truth

Reduce benchmark noise from hosted-authority ambiguity while preserving conservative claim discipline.

### 159 — top failure family elimination tranche

Use measured benchmark output to choose and eliminate the single biggest remaining one-task failure family.

### 160 — one-task promotion re-proof

Run a formal promotion re-proof to decide whether the bounded one-task lane is ready to become the default path for benchmark-eligible one-task work.

## Expected outcome of this slice

By the end of this roadmap slice, we should be able to say one of two things honestly:

1. the orchestrator is still not ready to become the default execution path for benchmark-eligible one-task work, and here are the measured blockers, or
2. the orchestrator is ready to become the default supervised path for benchmark-eligible one-task work, while multi-task remains gated.

Either outcome is useful, because both are grounded in real benchmark behavior rather than optimism.
