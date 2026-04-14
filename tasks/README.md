# Tasks README

## Current continuation order

- 171 — two-task pilot admission and eligibility truth
- 172 — dependency-aware adjacent-task handoff contract
- 173 — supervised dev/test role split for bounded pilot
- 174 — two-task canary scorecard and benchmark
- 175 — bounded two-task pilot re-proof and product checkpoint

## Execution note for 173

Task 173 is an **extension-only** bounded pilot task.

It must preserve existing frozen/public controller-contract and single-task reporting surfaces while adding explicit supervised builder/verifier separation for the bounded pilot lane.

Do not simplify or replace shared contract helpers when implementing Task 173.
