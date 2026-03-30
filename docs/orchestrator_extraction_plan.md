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

## Post-069 controller extraction status

A second controller extraction has now landed.

The orchestrator controller still lives in `agents/run_task.py`, but pure helper logic is no longer concentrated only there. The extracted modules are now:

- `agents/lib/task_contracts.py`
- `agents/lib/failure_artifacts.py`
- `agents/lib/protected_lane.py`
- `agents/lib/bundle_repair.py`

This further reduces direct responsibility in `agents/run_task.py` while preserving the current helper/public surface expected by the runtime and tests.

### What is now extracted

- explicit deliverable and task-contract policy helpers
- canonical docs path policy helpers
- protected/non-protected required-path partitioning helpers
- truthful placeholder and durable failure-artifact helpers
- protected-lane coordination helpers
- protected target profile and request-argument coordination helpers
- duplicate/conflicted bundle recovery helpers
- focused conflicted-file repair preparation helpers

### What remains to be decomposed

`agents/run_task.py` is still not fully decomposed. Higher-risk orchestration flow remains there, including:

- top-level shell execution coordination
- accepted-file reconciliation across multiple lanes
- controller sequencing across iterative task execution
- batch-oriented task queue, state, and resume orchestration
- user-facing policy decisions for continue/stop/manual escalation

### Next extraction priorities

The next controller-decomposition priorities should be:

1. task-list manifest and queue model
2. batch state persistence and resume
3. per-task checkpoint and branch-isolation coordination
4. explicit continue/stop/manual policy surfaces
5. user-facing batch runner CLI and summary artifacts

This keeps the decomposition incremental while preserving current runtime behavior and aligns the next tranche to 070–075.
