# Orchestrator Product Spec (In-Repo Productizing Engine)

## Product intent

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, and seam-aware testability.

## Current product stage

- **Post-048 baseline achieved** (042–048 complete)
- **049–052 complete on `main`**
- **Reliability/autonomy continuation complete through 067** (including 065a and 067a)
- **Protected/controller stabilization complete through 069** (including 068, 068a, 068b, and 068c)
- **070 adds task-list manifest and queue groundwork for backlog execution**
- **070b clarifies runtime-artifact lifecycle controls with explicit retention mode**
- **071 adds persisted batch-state and deterministic resume groundwork for queue execution**
- Product is reusable and increasingly standardized, but **not yet extracted** as a standalone repo/package and **not yet a full end-to-end backlog runner**

## Users and use cases

- Engineering operators running governed task workflows
- Projects requiring deterministic, policy-constrained automation
- Multi-project environments where adapter-driven portability matters
- Repositories that need stable test seams and guarded integrated coverage before extraction

## Core capabilities

- Structured task ingestion and contract parsing
- Safety harness with protected-file policies and semantic preflight checks
- Controlled execution shell and command routing
- Review/compliance/approval gates
- Backlog state tracking and recovery
- Audit logging and failure journaling
- Optional dry-run/simulation and safe parallelism
- Multi-project adapter support
- Stable seam registry for orchestrator integration testing
- Seam-aware preflight checks for task shape and generated bundles
- Lightweight task-scope / split heuristics for broad multi-seam tasks
- Deterministic task-list manifest parsing and queue construction
- Explicit manifest validation for missing task files and duplicate-path policy handling
- Runtime artifact quarantine with explicit operator retention controls for known-safe scratch files
- Persisted machine-readable batch state for task-list execution and deterministic resume

## Sequence summary

### Completed baseline (042–048)

- Harness modularization umbrella and extracted foundations
- Parser/policy and semantic preflight extraction
- Thin run-task shell parity
- Runtime artifact quarantine
- Two-phase spec execution and frozen-task mode
- Failure journal and retry context
- Project bootstrap adapter
- Verification plugins
- Safe parallelism

### Completed stabilization (049–052)

1. Shell convergence umbrella and dedupe
2. Public interface freeze hardening
3. Documentation/status normalization
4. Portability proof on a second project

### Completed continuation and stabilization follow-ons (053–069)

5. Stable seam registry
6. Task / seam preflight linter
7. One seam-aligned integrated capability E2E flow
8. Failure-journal live seam stabilization
9. Safe-parallelism / review integration stabilization
10. Runtime artifact quarantine integration stabilization
11. Extraction prep for future package/repo split
12. Canonical docs path policy
13. Reliability/autonomy continuation through 067 (plus 065a and 067a)
14. Task scope / split heuristics (068)
15. Protected/controller stabilization follow-ons (068a–068c)
16. Controller decomposition second extraction (069)

### Current backlog-execution groundwork (070)

17. Task-list manifest and deterministic queue model
18. Missing-file validation and duplicate-path policy handling for manifest inputs
19. Runtime wiring to support queue-oriented continuation work in later tasks

### Runtime artifact lifecycle clarity extension (070b)

20. Successful `--push` runs keep default safety: known-safe runtime scratch artifacts are quarantined/removed before staging
21. Operators can explicitly retain known-safe runtime artifacts (flag/env controlled) for debugging
22. Retained known-safe artifacts are still unstaged (`git rm --cached --ignore-unmatch`) to prevent accidental auto-commit
23. Unknown runtime artifacts remain protective blockers and are surfaced distinctly from known-safe retained/quarantined states
24. Lifecycle messaging is explicit across retained, quarantined-removed, and blocked-unknown outcomes

### Batch state persistence and resume groundwork (071)

25. Batch execution state is persisted as a narrow machine-readable JSON artifact containing manifest identity, ordered queue items, per-task status, current index, sequence counters, and timestamps
26. New batch state can be initialized directly from a validated manifest queue without replacing the single-task flow
27. Resume path validates manifest fingerprint identity; mismatched state/manifest combinations are rejected with explicit errors
28. Resume may enforce exact manifest source matching unless an explicit override rule is enabled
29. Queue status transitions are deterministic and narrow (`queued -> running`, `running -> completed|failed|manual_patch|blocked`) with invalid transitions rejected
30. Resume now also validates queue identity/ordering against the provided manifest-derived queue to prevent accidental resume on fingerprint-compatible but queue-divergent state

## Batch state file model (071)

The persisted batch state file is intentionally narrow and reusable:

- `state_version`: schema version for forward compatibility
- `manifest.source`: identity/path string used to initialize the batch
- `manifest.fingerprint`: deterministic digest over canonical manifest JSON
- `queue[]` ordered entries:
  - `task_path`
  - `ordinal`
  - `status`
  - `status_note`
  - `attempts`
  - `updated_seq`
- `current_index`: next queue position to process
- `event_seq`: monotonic transition counter
- `created_ts` / `updated_ts`: deterministic integer timestamps/counters supplied by caller
- `batch_status`: derived aggregate (`active|completed|blocked|failed|manual_patch`)

Design constraints:

- no speculative parallel semantics in the state shape
- no git-history coupling and no external-service dependency
- deterministic counters/ordering suitable for replay and later orchestration layers

## Resume behavior rules (071)

- **Start new batch**: initialize from manifest + constructed queue, all task statuses begin as `queued`
- **Resume existing batch**: load persisted state and require manifest fingerprint match
- **Mismatched manifest**: fail fast with explicit mismatch error
- **Manifest source mismatch**: fail by default; optional override can allow path/source mismatch when operator intends it
- **Queue mismatch on resume**: fail fast when persisted state queue paths/order do not match the supplied manifest-derived queue
- **Current index advancement**: advances only after terminal transition on the currently running item, preserving deterministic ordering

## Safe transition policy (071)

Allowed transitions are intentionally narrow:

- `queued -> running`
- `running -> completed`
- `running -> failed`
- `running -> manual_patch`
- `running -> blocked`

All other transitions are invalid and rejected. This keeps resume stable, prevents silent rewinds/skips, and gives later backlog runners explicit control points.

## Runtime artifact lifecycle policy

Known-safe runtime scratch artifacts include files such as:

- `last_output.txt`
- `_last_agent_model_output.txt`
- `_last_agent_file_bundle.txt`

Default posture on successful push flow:

- remove these known-safe scratch artifacts from disk as part of quarantine cleanup
- unstage them from index before staging (`git rm --cached --ignore-unmatch`)
- prevent accidental commit drift from temporary runtime files

Explicit retention mode:

- operators may opt in to retain known-safe scratch artifacts on disk for forensic/debug review
- retention is narrow and explicit (flag/env driven), never implicit default behavior
- even when retained, known-safe artifacts remain unstaged by default controller behavior

Unknown runtime artifacts:

- are never treated as known-safe retained scratch
- continue to trigger protective blocking behavior until resolved
- are messaged as blocked unknowns, distinct from known-safe retention/removal

## Packaging and repo strategy

- **Now**: continue in the current repo through the backlog-execution tranche so queue/state/resume/isolation behavior is proven before extraction
- **Later**: execute extraction once the continuation and backlog-execution surfaces are stable, documented, and validated under test

## Intended package-level public surface (`builder.orchestrator`)

The package root should provide a deliberate, orchestrator-only import surface for external callers and future extraction consumers.

Current intentional re-exports at package level:

- `ProjectConfig`
- `GenericProjectConfig`
- `load_project_config`
- `bootstrap_project_config_scaffold`
- `ProjectAdapter`
- `load_project_adapter`
- `bootstrap_project_adapter_scaffold`
- `build_bootstrap_starter_docs_text`
- `build_bootstrap_task_template_text`

Design rules:

- Re-export orchestrator-facing configuration and adapter contracts only.
- Keep module-level import paths stable and available (for compatibility and migration safety).
- Do **not** re-export TradingBot runtime modules from `builder.orchestrator`.
- Avoid catch-all or wildcard export patterns that obscure the supported API.

## Success criteria for extraction readiness

- Stable public interfaces with tested compatibility
- Stable seam registry for orchestrator integration tests
- Preflight can catch common seam/task-shape mistakes early
- Demonstrated portability beyond the primary project
- One integrated E2E flow validated under current live contracts
- Focused seam-family hardening completed
- Task-list manifest and queue semantics validated under test
- Batch state / resume / isolation surfaces completed and documented
- Documentation/state surfaces synchronized and unambiguous

## Bootstrap lane rule

The orchestrator should support both an autonomous task lane and a manual patch lane. The first harness-bootstrap tasks in the reliability/recovery/autonomy tranche use the manual patch lane to avoid self-modification regressions while the stable contract is being frozen.

## Canonical docs placement

This product spec lives under `docs/` because orchestrator/tradingbot narrative documents are canonical there. `README.md` remains the only canonical root-level README; do not create duplicate root-level `ORCHESTRATOR_*.md` or `TRADINGBOT_*.md` narrative docs when the `docs/` path is the intended source of truth.
