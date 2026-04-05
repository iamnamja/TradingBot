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

## Post-075 controller extraction status

The orchestrator controller still lives in `agents/run_task.py`, but pure helper logic is no longer concentrated only there. The extracted modules now include:

- `agents/lib/task_contracts.py`
- `agents/lib/failure_artifacts.py`
- `agents/lib/protected_lane.py`
- `agents/lib/bundle_repair.py`
- `agents/lib/task_queue.py`
- `agents/lib/batch_state.py`

This is materially better than earlier in the project, but `agents/run_task.py` still owns too much end-to-end orchestration.

### What remains inline

Higher-risk orchestration flow still concentrated in `agents/run_task.py` includes:

- final acceptance review reconciliation
- retryable acceptance-failure self-heal orchestration
- accepted-task PR/check/merge/reset lifecycle
- cross-task batch executor sequencing
- resume-after-merge and resume-after-manual-resolution decisions

### Next extraction priorities

The next controller-decomposition priorities should be:

1. final acceptance reviewer/report surface
2. batch executor/controller loop
3. accepted-task git workflow / merge-reset helpers
4. resume-after-merge and manual-resolution helpers
5. remaining outer shell routing/orchestration compatibility wrappers

This keeps the decomposition incremental while preserving current runtime behavior and aligns the next tranche to 076–082.
