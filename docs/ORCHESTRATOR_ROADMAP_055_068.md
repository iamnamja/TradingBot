# Orchestrator Roadmap — Reliability / Recovery / Autonomy Continuation (055–068 + stabilization extension)

## Why this reset exists

The original 055+ continuation was aimed at integrated coverage and extraction prep, but recent execution history showed that the orchestrator still needed stronger **recovery**, **task-family routing**, **semantic validation**, and **control-plane behavior** before it could reliably move through long backlogs without repeated human intervention.

That tranche landed useful improvements, but post-067 execution still showed a gap between:

- successful ordinary task execution
- protected/controller-file autonomy
- malformed-bundle recovery for controller work
- the long-term goal of making `agents/run_task.py` materially less monolithic

This roadmap therefore inserts a short **stabilization extension** before the original Task 068 resumes.

## Completed tranche

The following reliability/autonomy continuation now appears complete:

- 055 — Reliability and Autonomy Umbrella
- 055a — Harness Contract Freeze
- 055b — Task Family Classifier, Prompt Compiler, and Split Strategy
- 055c — Seam Manifest and Semantic Contract Validator
- 056 — Failure Classifier and Remediation Planner
- 057 — Localized Repair and Failure Artifacts
- 058 — Backlog Readiness and State Engine
- 059 — CI / PR / Merge Controller
- 060 — Autonomy Loop Integration
- 061 — Continuation Reset and Numbering Sync
- 062 — Integrated Capabilities E2E
- 063 — Failure Journal Live Seam
- 064 — Safe Parallelism / Review Integration
- 065 — Runtime Artifact Quarantine Integration
- 065a — Deliverable Completeness Enforcement
- 066 — Package Extraction Prep
- 067 — Canonical Docs Path Policy
- 067a — Protected Method Mode Routing and Failure Artifact Fix

## New stabilization extension (run in this order)

### 068a — Protected Lane Execution Hardening
Turn protected-file detection into a working protected execution lane, especially for mixed protected/non-protected tasks.

### 068b — Duplicate Bundle Normalization and Focused Repair
Recover from duplicate `FILE:` path bundles by normalizing safe duplicates or retrying only the conflicted files.

### 068c — Controller Decomposition and First Extraction
Start making `agents/run_task.py` less monolithic by extracting pure task-contract and failure-artifact helpers into dedicated modules.

## Deferred continuation (resume after 068a–068c)

### 068 — Task Scope / Split Heuristics
The original Task 068 remains valid, but it is no longer the immediate next task. The orchestrator needs the stabilization extension above before broader task-scope/split guidance will be trustworthy in practice.

## Why 068 moved behind 068a–068c

Recent execution history showed:

- protected/controller tasks still require disproportionate manual intervention
- malformed bundles can still derail controller tasks even after truthful artifacts improve
- `run_task.py` remains too central, making controller fixes fragile and regression-prone

Task-scope/split heuristics still matter, but they are less urgent than making protected/controller execution reliable and shrinking the controller surface itself.

## Lane guidance

- **Likely manual-patch / protected-controller lane**
  - 068a
  - 068c
- **Expected autonomous lane once 068a lands**
  - 068b
  - 068

## Immediate next task

After the docs/tasks planning update is merged, the next task to execute is:

`tasks/068a_orchestrator_protected_lane_execution_hardening.md`
