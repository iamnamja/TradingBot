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
- allowlisted one-task autonomous execution
- deterministic run ledger, canary reporting, and supervised handoff artifacts

## Next policy posture (143–148)

The next tranche should keep the lane narrow while making it more operationally trustworthy:

- hosted-authority probing should distinguish `not yet reported` from truly missing or failed required checks
- live `ci-required` convergence should be smoke-proved on a real PR before claims broaden
- the orchestrator scheduler should route only the single-ready-safe-task case through the bounded runner
- mixed safe and supervised-only queues should stop/requeue conservatively instead of widening autonomy
- bounded single-task resume/re-entry should be idempotent and artifact-safe
- broader autonomy claims should remain blocked until the live canary proof bundle is green
