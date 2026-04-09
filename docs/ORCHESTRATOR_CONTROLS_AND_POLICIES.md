# Orchestrator Controls and Policies

This document describes the stable seams intended for orchestrator integration tests and monkeypatch-based verification, plus the current controller-policy posture.

## Stable seam registry

The orchestrator shell exposes a registry of supported seam families through:

- `agents.run_task._shell_router_exports()`
- `agents.lib.shell_router.build_shell_seam_registry()`
- `agents.lib.shell_router.shell_seam_exports()`

The registry is intentionally small and stable. It is meant to replace ad hoc lookups of private globals such as `run_task.some_internal_name`.

## Supported seam families

The current canonical family names are:

- `bootstrap`
- `spec_mode`
- `failure_journal`
- `validator_runner`
- `artifact_quarantine`
- `runtime_foundations`
- `parser_policy`
- `semantic_preflight`
- `shell_router`

## Current control posture

After Tasks 137–142, the orchestrator now has bounded deterministic defenses around:

- proof-task admission and exact deliverable contracts
- bundle failure classification and missing-deliverable retry compilation
- coupled compatibility-surface repair planning
- last-known-good subset preservation during retries
- hosted-authority operational-readiness truth
- a safe task-family autonomy allowlist for ordinary one-task work
- deterministic single-task ledger, canary metrics, recovery reporting, and supervised handoff artifacts

## Active policy posture

The current tranche still does **not** broaden into arbitrary autonomy. The active policy remains a narrow safe lane:

- autonomous execution is allowed only for explicitly allowlisted ordinary task families
- the safe lane currently covers docs/tests/`src/tradingbot` work only, while `agents/` and `src/builder/orchestrator/` remain escalation-first by default
- proof-shaped tasks remain supervised even when their file families are otherwise allowlisted
- self-hosting control-plane edits remain escalation-first unless separately proven safe
- unattended readiness remains blocked unless real GitHub required-check reporting and enforcement are visibly converged
- broader autonomy claims remain blocked until the safe lane is re-proven green under live hosted authority
