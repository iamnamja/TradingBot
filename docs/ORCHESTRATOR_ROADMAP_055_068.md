# Orchestrator Roadmap — Reliability / Recovery / Autonomy Continuation (055–068)

## Why this reset exists

The original 055+ continuation was aimed at integrated coverage and extraction prep, but recent execution history showed that the orchestrator still needs stronger **recovery**, **task-family routing**, **semantic validation**, and **control-plane behavior** before it can reliably move through long backlogs without repeated human intervention.

This roadmap inserts a new active tranche at **055–061** focused on turning the orchestrator into a resilient controller, then resumes the deferred continuation at **062–068**.

## Active tranche (run in this order)

### 055 — Reliability and Autonomy Umbrella
Umbrella only. This task is for framing, docs, and acceptance of the tranche. Do **not** run it as a normal autonomous implementation task.

### 055a — Harness Contract Freeze
Freeze the stable runner/shell contract and lock the surfaces that future reliability work depends on.
- Runner / shell compatibility
- Baseline loading / protected target contract
- Stable helper and message surfaces
- Manual patch lane

### 055b — Task Family Classifier, Prompt Compiler, and Split Strategy
Teach the orchestrator to recognize task families and compile the correct request strategy for each.
- Docs-only
- Narrow tests-only
- Integration-test
- Protected harness/meta
- Split/defer when too broad

### 055c — Seam Manifest and Semantic Contract Validator
Replace brittle seam heuristics with explicit manifests and semantic validation.
- Exact seam names
- Allowed export keys
- Contract-aware preflight
- Manual patch lane

### 056 — Failure Classifier and Remediation Planner
Turn failures into structured remediation decisions.
- Retry vs localized repair vs task patch vs runner patch vs manual lane vs escalate
- Confidence-gated autonomy

### 057 — Localized Repair and Failure Artifacts
Make localized repair the default for small bundles and guarantee usable failure artifacts.
- Preserve good files
- Retry only bad files
- Always write real diagnostics

### 058 — Backlog Readiness and State Engine
Make task readiness, blockers, and next-task selection first-class orchestrator behavior.
- Backlog state
- Runnable task selection
- Blocked / deferred / split awareness

### 059 — CI / PR / Merge Controller
Bring PR creation, CI polling/classification, merge, and resync into the orchestrator control loop.

### 060 — Autonomy Loop Integration
Prove the orchestrator can combine readiness, routing, validation, remediation, localized repair, and PR/CI/merge into one control loop.

### 061 — Continuation Reset and Numbering Sync
Finalize the reset and hand the system back to the deferred continuation under the new numbering.

## Deferred continuation (resume only after 055–061)

### 062 — Integrated Capabilities E2E
Formerly `055_orchestrator_integrated_capabilities_e2e.md`

### 063 — Failure Journal Live Seam
Formerly `056_orchestrator_failure_journal_live_seam.md`

### 064 — Safe Parallelism / Review Integration
Formerly `057_orchestrator_safe_parallelism_review_integration.md`

### 065 — Runtime Artifact Quarantine Integration
Formerly `058_orchestrator_runtime_artifact_quarantine_integration.md`

### 066 — Package Extraction Prep
Formerly `059_orchestrator_package_extraction_prep.md`

### 067 — Canonical Docs Path Policy
Formerly `060_orchestrator_canonical_docs_path_policy.md`

### 068 — Task Scope / Split Heuristics
Formerly `061_orchestrator_task_scope_and_split_heuristics.md`

## Lane rules

- **Manual patch lane**
  - 055a
  - 055c
- **Autonomous lane**
  - 055b
  - 056
  - 057
  - 058
  - 059
  - 060
  - 061
  - Deferred continuation 062–068 after the tranche lands

## First task to run

After the docs/tasks renumbering patch is merged, the first task to execute is:

`tasks/055b_orchestrator_task_family_classifier_prompt_compiler_and_split_strategy.md`
