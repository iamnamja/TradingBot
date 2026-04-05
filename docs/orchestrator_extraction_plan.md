# Orchestrator Extraction Plan (Prep Only)

## Scope of this document

This document defines the concrete, ordered plan to extract the orchestrator into a standalone package/repository **after** stabilization gates are complete. It is planning and sequencing only; it does not indicate extraction is already done.

## Preconditions (must be true before extraction starts)

1. Reliability/autonomy continuation stabilization is complete (053–061 outcomes locked and validated).
2. Deferred continuation hardening work impacting interfaces is complete (062–068 outcomes validated).
3. Public orchestrator API surface is explicitly defined and tested at package root (`builder.orchestrator`).
4. Module-level compatibility contracts from 050–052 remain green under test.
5. Documentation and task status surfaces are synchronized in `docs/` and `tasks/README.md`.

If any precondition is unmet, extraction is deferred.

## Target package boundary

### In scope for extraction

- `src/builder/orchestrator/*` (orchestrator engine modules)
- minimal packaging metadata and CI/test harness needed to run orchestrator independently
- orchestrator-facing docs copied/adapted from canonical `docs/` sources

### Out of scope for extraction

- TradingBot runtime modules under `src/tradingbot/*`
- TradingBot product lifecycle and strategy/risk/execution code
- monorepo-only workflows unrelated to orchestrator operation

## Ordered execution sequence

1. **Freeze surface and tests**
   - Keep package-level exports intentional and explicit in `builder.orchestrator`.
   - Ensure smoke tests validate orchestrator package surface only.
   - Verify no TradingBot symbols are re-exported from orchestrator package root.

2. **Cut extraction branch and scaffold target repo**
   - Create extraction branch from a green baseline.
   - Initialize new repository/package scaffold for orchestrator.

3. **Copy orchestrator code with history-aware strategy**
   - Move/copy `src/builder/orchestrator` content into target layout.
   - Preserve commit traceability (e.g., subtree/filter strategy) where practical.

4. **Rewire imports and packaging metadata**
   - Update internal imports as required by new package root.
   - Add standalone package metadata, tooling config, and test entry points.

5. **Port and validate tests**
   - Bring orchestrator-specific tests first (unit + integration seams).
   - Remove or replace monorepo-coupled test assumptions.
   - Achieve green lint + tests in extracted repo.

6. **Back-compat bridge in monorepo (temporary)**
   - Keep monorepo compatibility path for defined transition window.
   - Document deprecation timeline and migration instructions.

7. **Consumer migration**
   - Update internal callers to new package coordinates.
   - Validate behavior parity in CI and representative workflows.

8. **Finalize split**
   - Remove temporary bridge after migration window closes.
   - Mark extraction complete in docs and status trackers.

## Risk controls

- No extraction while active interface churn is ongoing.
- Keep extraction changes isolated from feature work.
- Require parity checks (behavior + tests) before cutover.
- Maintain explicit rollback path to in-repo orchestrator state until migration completes.

## Definition of done (for future extraction execution)

- Standalone orchestrator repo/package is green in CI.
- Documented public API surface is preserved.
- Monorepo callers migrated or bridged during approved transition.
- Canonical documentation updated to reflect post-split ownership and usage.



## Post-081 controller extraction status

A third controller extraction has now landed.

The orchestrator controller still lives in `agents/run_task.py`, but the shell is thinner again and more controller families now have explicit homes outside the monolithic entrypoint.

### What is now extracted

The extracted modules now own these controller families:

- `agents/lib/task_contracts.py` — task/deliverable contract parsing and policy helpers
- `agents/lib/failure_artifacts.py` — truthful placeholder and durable failure-artifact helpers
- `agents/lib/protected_lane.py` — protected-lane coordination helpers
- `agents/lib/bundle_repair.py` — duplicate/conflicted bundle recovery helpers
- `agents/lib/final_acceptance.py` — final acceptance review/report classification and self-heal feedback helpers
- `agents/lib/batch_executor.py` — canonical sequential batch executor/controller loop and resume-preparation helpers
- `agents/lib/git_workflow.py` — accepted-task PR/merge/reset workflow helpers and branch-push guidance

### What remains inline in `agents/run_task.py`

Higher-risk shell coordination still remains inline, including:

- prompt construction and iterative retry/repair loop sequencing
- file-bundle application, snapshot restore, and localized failure feedback wiring
- check execution and policy orchestration across multiple helper families
- top-level CLI and single-task execution shell behavior

### Next extraction priorities

The next controller-thinning priorities after this pass should be:

1. prompt/retry controller decomposition
2. file-bundle transport + localized repair controller extraction
3. final single-task success path / push flow shell reduction
4. batch-runner proof wiring for autonomous merge-and-continue operation

This keeps the decomposition incremental while preserving current behavior and aligns the remaining inline work to 082 and beyond.
