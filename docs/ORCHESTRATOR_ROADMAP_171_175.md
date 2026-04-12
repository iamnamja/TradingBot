# Orchestrator Roadmap 171–175

## Theme

Bounded two-task pilot preparation under supervision.

## Why this slice exists

Tasks 166–170 tightened one-task promotion truth and defined a conservative path toward bounded multi-task work. The repo is now conditionally ready under supervision for one-task work, but a two-task pilot still needs mechanical admission, deterministic adjacent-task handoff, explicit supervised builder/verifier separation, and measured canary truth before it can be justified.

This slice is not broad multi-task autonomy. It is the smallest credible supervised two-task pilot preparation slice.

## Runtime posture shaping this slice

- The Task 170 gate already exists in `agents.lib.task_queue`; Task 171 should refine that surface rather than inventing a new one.
- The runtime already has adjacent-task truth surfaces such as `depends_on`, `next_task_may_proceed`, and supervised handoff artifacts; Task 172 should reuse them.
- The runtime already has a `controller` / `builder` / `verifier` role model; Task 173 should make that split explicit for the pilot rather than adding new role types.
- The runtime already has a durable benchmark and promotion surface; Tasks 174–175 should extend that same lane.

## Tasks

### 171 — two-task pilot admission and eligibility truth
Make pilot admission mechanical and threshold-based by consuming the existing one-task promotion truth.

### 172 — dependency-aware two-task handoff contract
Define the adjacent-task handoff truth that task two requires before starting.

### 173 — supervised dev-test role split for bounded pilot
Make the existing builder/verifier split explicit while preserving controller authority.

### 174 — two-task canary scorecard and benchmark
Measure the bounded pilot lane with durable canary truth.

### 175 — bounded two-task pilot re-proof and product checkpoint
Decide whether a bounded supervised two-task pilot is justified and whether productization remains blocked.

## Exit signal

Do not claim general multi-task autonomy or the separate orchestrator app phase at the end of this slice unless the bounded pilot re-proof explicitly justifies the next widening step.
