# Orchestrator Controls and Policies

This document describes the stable seams intended for orchestrator integration tests and monkeypatch-based verification, plus the current controller-policy posture.

## Current control posture

The orchestrator now has bounded deterministic defenses around:

- proof-task admission and exact deliverable contracts
- bundle failure classification and missing-deliverable retry compilation
- coupled compatibility-surface repair planning
- hosted-authority operational-readiness truth around `ci-required`
- explicit safe-lane allowlisting for ordinary one-task work only
- scheduler routing through the bounded one-task runner only when exactly one safe task is ready
- explicit supervised handoff, requeue, and stop posture for mixed queues
- bounded resume semantics that do not widen scope or duplicate durable artifacts

## Current policy boundary

The autonomous lane is intentionally narrow:

- autonomous execution is allowed only for explicitly allowlisted ordinary task families
- `agents/` and `src/builder/orchestrator/` remain escalation-first by default
- proof-shaped tasks remain supervised unless separately proven safe
- mixed queues stop after at most one admitted safe task and then hand off/requeue conservatively
- broader autonomy claims remain blocked until live canary evidence repeatedly stays green
