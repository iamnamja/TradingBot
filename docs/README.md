# Docs Index Addendum

## Active tranche

Current active tranche: 201-205.

## Current roadmap slice

- `ORCHESTRATOR_ROADMAP_201_205.md` — convert the admitted three-step canary surface into real supervised execution proof and a cautious adjacent-manifest gate
- `ORCHESTRATOR_PHASE_DIRECTION.md` — agreed phase order: truthful one-task path first, bounded supervised two-task pilot second, reliability hardening next, contract/model compatibility next, transport stability and observability next, post-transport execution reproof next, only then cautious bounded widening, standalone app last
- `ORCHESTRATOR_CAUTIOUS_BOUNDED_WIDENING_201_205.md` — operator-facing rules, artifact expectations, and working cadence for the 201-205 tranche

## Current continuation note

Tasks 196-200 completed the post-transport execution reproof tranche:
- Task 196: post-transport one-task rebenchmark and empty-output regression guard
- Task 197: transport-stable bounded two-task pilot rerun and scorecard refresh
- Task 198: adjacent-pair resume precision truth
- Task 199: supervised three-step canary admission and chain contract
- Task 200: post-transport execution checkpoint and bounded next-slice gate

Tasks 201-205 now target the next conservative step:
- Task 201: supervised three-step canary runner and durable chain ledger
- Task 202: curated three-step canary corpus and manifest truth
- Task 203: three-step canary benchmark and supervision-aware scorecard
- Task 204: controller route trace and resume reconstruction for chained canary runs
- Task 205: supervised multi-task canary checkpoint and adjacent-manifest gate

## Current next-step note

The near-term focus stays conservative:

- keep one-task as the default proving path
- keep the bounded supervised two-task pilot as the only already-proven multi-task form
- convert the admitted three-step canary contract into real, explicitly supervised execution proof before widening any further
- make controller route decisions more durable and reconstructable across interrupted canary runs
- allow any next widening step only if a new checkpoint can defend a tiny adjacent-manifest gate under supervision

## Post-200 checkpoint note

The post-200 checkpoint allows planning to continue only within narrow supervised shapes. It does not authorize broad autonomy. The strongest proven path remains one task under supervision, followed by a bounded supervised two-task pilot. The three-step canary shape is admitted, but it still needs real runner, corpus, and scorecard proof before it should be treated as an operational path.

## Why the 201-205 tranche exists

The repo now has the smallest honest widening contract beyond the bounded two-task pilot, but not yet the real execution evidence to trust that shape in practice.

This tranche exists to convert that admitted canary surface into durable operational truth:

- exactly-three adjacent task execution only,
- explicit supervision accounting,
- durable controller-route and resume truth,
- benchmark artifacts that separate direct chain progress from supervision-assisted progress,
- and a final checkpoint that decides whether a tiny adjacent-manifest gate is justified.

## Scope honesty reminder

This tranche is still not about arbitrary scheduling, unattended autonomy, or a fully extracted orchestrator product. It is about one more bounded step:

- from a contract-only three-step canary shape,
- to a real supervised three-step canary execution path,
- and only then to a tiny adjacent-manifest gate if the evidence is strong enough.

## New runtime seam (Task 201)

A supervised three-step canary runner now exists at:
- `agents/lib/three_step_canary.py`

It accepts exactly three explicitly admitted adjacent tasks (A->B->C under strict adjacency), requires supervision, and persists a durable chain ledger under:
- `<artifacts_dir>/three_step_canary/<session_id>/chain_ledger.json`

The ledger records chain/session id, task ids and order, adjacency truth for A->B and B->C, supervision truth, resume truth per adjacent pair, and the terminal chain outcome.

A test proving acceptance, adjacency validation, durable ledgers, and conservative rejection of malformed shapes is included:
- `tests/test_three_step_canary.py`
