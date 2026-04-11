# Task 164: orchestrator runtime artifact hygiene and typo normalization

Goal

Normalize runtime artifact naming and retention so proof-mode runs produce clear, predictable artifacts without ambiguous typos or misleading leftovers.

Why this matters

During the first reliability sprint, runtime artifact handling improved, but there were still confusing leftovers and at least one typo-shaped runtime artifact path. That kind of noise makes one-task diagnosis harder than it should be.

Create or update these exact files
- agents/run_task.py
- agents/lib/artifact_quarantine.py
- agents/lib/project_workspace_adapter.py
- tests/test_runtime_artifact_quarantine.py
- tasks/164_orchestrator_runtime_artifact_hygiene_and_typo_normalization.md
- docs/TRADINGBOT_PROJECT_STATE.md

Scope
- Remove or normalize typo-shaped runtime artifact names.
- Ensure retained known-safe runtime artifacts are named consistently.
- Keep unknown runtime artifacts blocked, but make the known-safe set more predictable and easier to inspect.
- Ensure workspace artifact path reporting matches the actual retained artifact policy.

Acceptance criteria
- No typo-shaped runtime artifact names remain in the active runtime path.
- Runtime artifact allowlists and workspace artifact paths are aligned.
- Tests cover known-safe retention, blocked unknown leftovers, and normalized artifact naming.
- Docs mention that proof-mode artifact hygiene is now explicit and predictable.

Notes
- Keep this task strictly runtime-facing.
- Do not broaden into task scoring or scheduler behavior.
