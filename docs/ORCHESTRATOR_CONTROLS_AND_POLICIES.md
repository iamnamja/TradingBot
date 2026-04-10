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

After Tasks 124–148, the orchestrator now has bounded deterministic defenses around:

- proof-task admission and exact deliverable contracts
- bundle failure classification and missing-deliverable retry compilation
- coupled compatibility-surface repair planning
- last-known-good subset preservation during retries
- hosted-authority operational-readiness truth
- conservative stop when no dependency-ready task is available
- a narrow one-task autonomous lane with scheduler bridging, handoff, resume, and proof artifacts

## Next policy posture (149–154)

The next tranche should optimize for **external-safe one-task execution quality**:

- the primary proving ground is a canonical external-safe evaluation corpus, not arbitrary self-hosting work
- the bounded one-task lane should behave like a real dev / test / repair / controller loop
- targeted self-heal should be ranked around ordinary external-safe failure classes, not generic replay
- pass-rate measurement should drive readiness decisions
- self-hosting control-plane edits remain escalation-first unless separately proven safe later
- multi-task widening remains blocked until the one-task external-safe pass-rate gate is green
- standalone app packaging remains downstream of measured run quality, not a substitute for it
