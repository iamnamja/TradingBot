# Task 176 — orchestrator bounded two-task pilot runner and pair ledger

## Why

Tasks 171–175 proved that a bounded supervised two-task pilot is ready in principle, but most of that truth is still preparation and canary truth. The repo now needs a real runner for exactly-two-task pilot execution so pair-level evidence does not remain synthetic or implicit.

## Scope

Add a bounded supervised two-task pilot runner that executes exactly two adjacent tasks and writes a durable pair-level session ledger.

## Runtime seams to reuse

- Reuse the admission and eligibility truth from Task 171.
- Reuse the adjacent A->B handoff contract from Task 172.
- Reuse the bounded pilot role split from Tasks 173a/173b.
- Reuse existing single-task durability and reporting surfaces where possible.
- Reuse the benchmark/canary artifact directory conventions established in Tasks 174–175.

## Requirements

- Accept exactly two tasks in the bounded pilot run.
- Reject or stop conservatively if:
  - fewer than two tasks are supplied,
  - more than two tasks are supplied,
  - the second task is not an explicit adjacent/handoff-eligible follow-on to the first task,
  - admission truth blocks the pair.
- Persist a durable pair ledger that records at minimum:
  - pair/session id,
  - task A and task B identifiers,
  - admission decision,
  - handoff status,
  - role-sequence/checkpoint summary,
  - whether supervision was required,
  - terminal pair outcome.
- Keep the runner explicitly bounded to two tasks only.
- Do **not** add a general multi-task scheduler in this task.

## Non-goals

- Do not support arbitrary-length manifests.
- Do not widen beyond supervised two-task pilot work.
- Do not change the one-task benchmark or promotion surfaces.

## Acceptance criteria

- Tests prove the runner accepts exactly two tasks and rejects broader manifests conservatively.
- Tests prove pair ledgers are written durably and include admission/handoff/supervision truth.
- Tests prove blocked or incompatible pairs stop explicitly rather than silently continuing.
