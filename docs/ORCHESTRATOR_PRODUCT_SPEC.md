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
