# Orchestrator Extraction Plan (Prep Only)

## Scope of this document

This document defines the concrete, ordered plan to extract the orchestrator into a standalone package/repository **after** stabilization gates are complete. It is planning and sequencing only; it does not indicate extraction is already done.

## Preconditions (must be true before extraction starts)

1. Reliability/autonomy continuation stabilization is complete.
2. Backlog execution foundations and ordinary-manifest autonomy proof are complete and green.
3. Controller-facing contracts are stable and documented.
4. Public orchestrator API surface is explicitly defined and tested.
5. Documentation and task status surfaces are synchronized in `docs/` and `tasks/README.md`.

If any precondition is unmet, extraction is deferred.

## Post-082 status

The repo now has:

- a canonical batch executor loop
- accepted-task PR/check/merge/reset posture
- resume-after-merge and manual-resolution semantics
- further controller extraction out of `agents/run_task.py`
- a first narrow ordinary-manifest autonomous proof

But extraction should still be deferred until the next tranche stabilizes:

- canonical controller contract
- non-reexecuting retry/self-heal semantics
- merge/reset truth persistence
- controller strict-mode / patch-quality discipline

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

2. **Stabilize controller contracts**
   - Canonicalize controller decisions, merge truth fields, and resume metadata.
   - Ensure controller-facing tests/docs use one contract vocabulary.

3. **Finish controller thinning**
   - Continue extracting strict-mode/repair-context/controller glue from `agents/run_task.py`.
   - Preserve shell wrappers only where compatibility needs them.

4. **Cut extraction branch and scaffold target repo**
   - Create extraction branch from a green baseline.
   - Initialize new repository/package scaffold for orchestrator.

5. **Copy orchestrator code with history-aware strategy**
   - Move/copy `src/builder/orchestrator` content into target layout.
   - Preserve commit traceability where practical.

6. **Rewire imports and packaging metadata**
   - Update internal imports as required by new package root.
   - Add standalone package metadata, tooling config, and test entry points.

7. **Port and validate tests**
   - Bring orchestrator-specific tests first.
   - Remove or replace monorepo-coupled test assumptions.
   - Achieve green lint + tests in extracted repo.

8. **Back-compat bridge in monorepo**
   - Keep monorepo compatibility path for defined transition window.
   - Document deprecation timeline and migration instructions.

9. **Consumer migration**
   - Update internal callers to new package coordinates.
   - Validate behavior parity in CI and representative workflows.

10. **Finalize split**
   - Remove temporary bridge after migration window closes.
   - Mark extraction complete in docs and status trackers.

## Current extraction priorities after 082

The most useful controller-thinning priorities before extraction are now:

1. canonical controller contract surfaces
2. strict-mode and patch-quality gating helpers
3. semantic failure digest / repair-context helpers
4. final single-task success-path shell reduction
5. remaining controller glue around proof/merge/reset sequencing

## Definition of done (for future extraction execution)

- Standalone orchestrator repo/package is green in CI.
- Documented public API surface is preserved.
- Controller-facing contracts are stable and documented.
- Monorepo callers migrated or bridged during approved transition.
- Canonical documentation updated to reflect post-split ownership and usage.
