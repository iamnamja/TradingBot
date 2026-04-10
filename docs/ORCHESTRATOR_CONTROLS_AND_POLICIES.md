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

After Tasks 124–136, the orchestrator now has bounded deterministic defenses around:

- proof-task admission and exact deliverable contracts
- bundle failure classification and missing-deliverable retry compilation
- coupled compatibility-surface repair planning
- last-known-good subset preservation during retries
- hosted-authority operational-readiness truth
- conservative stop when no dependency-ready task is available

## Next policy posture (143–148)

The next tranche should **not** broaden into arbitrary autonomy. It should narrow into a safe lane:

- autonomous execution is allowed only for explicitly allowlisted ordinary task families
- the safe lane admits narrow docs/tests/`src/tradingbot` work only, while `agents/` and `src/builder/orchestrator/` remain escalation-first by default
- self-hosting control-plane edits remain escalation-first unless separately proven safe
- unattended readiness remains blocked unless real GitHub required-check enforcement is converged
- a dedicated single-task runner should emit a run ledger, canary metrics, explicit escalation artifacts, and deterministic resume-state artifacts
- resumed one-task runs must be idempotent: no duplicate ledger rows, no duplicate supervised artifacts, and no widened execution scope
- broader autonomy claims should remain blocked until the safe lane is re-proven green
