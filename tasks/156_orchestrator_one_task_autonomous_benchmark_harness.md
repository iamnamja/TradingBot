# Task 156 — orchestrator one-task autonomous benchmark harness

## Why

Tasks 149–155 built a meaningful bounded one-task lane, but we have still been proving it mostly by manually applying curated patches and then repairing regressions outside the lane. The next phase must switch from “building more orchestrator plumbing” to “using the orchestrator itself as the thing under test.”

The goal of this task is to establish a benchmark harness that treats orchestrator-run one-task execution as the primary proof surface.

## Scope

Add a benchmark harness for the external-safe one-task lane that can:

1. load a curated set of benchmark-eligible tasks from the canonical external-safe corpus/eval manifest,
2. execute them one at a time through the existing bounded one-task runner path,
3. record a run-level benchmark verdict per task,
4. persist a benchmark session artifact that distinguishes:
   - completed directly,
   - completed after bounded self-heal,
   - failed without completion,
   - authority-blocked,
   - supervised/escalated,
5. explicitly mark any human mid-run intervention as a failed autonomous benchmark run,
6. preserve existing one-task truth and not widen the lane to two-task execution.

## Requirements

- Reuse the current bounded one-task runner and ledger surfaces instead of inventing a parallel execution engine.
- Keep the benchmark harness external-safe only.
- The benchmark harness must be able to run a selected subset of benchmark tasks or the full benchmark set.
- Benchmark session artifacts must be written under a stable artifacts path.
- Benchmark results must be machine-readable JSON.
- A benchmark run must preserve the distinction between direct completion and completion after bounded self-heal.
- A benchmark run must record whether the result was blocked by hosted-authority truth.
- The task must not widen autonomous execution claims beyond the current one-task lane.

## Acceptance criteria

- There is a stable benchmark harness entrypoint for one-task external-safe trials.
- There are tests proving benchmark session artifact creation and result categorization.
- There are tests proving that a manual-intervention flag yields a failed autonomous benchmark result.
- There are tests proving that two-task or mixed-lane execution is still out of scope.
- Project docs describe the benchmark harness as the current proving mode for the orchestrator.

## Notes

This task is the first task in the new proof-mode tranche. It should make it easy for us to run the orchestrator on real one-task work and grade the system honestly.
