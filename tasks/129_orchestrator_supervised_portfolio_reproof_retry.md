# Task 129 — Orchestrator supervised portfolio re-proof retry

## Goal
Rerun the bounded supervised multi-project portfolio proof after Tasks 124–128 land.

## Scope
- start from clean `main`
- bounded supervised local-first lane only
- preserve project isolation, dependency-aware selection, hosted-authority truth, and conservative stop posture

## Required changes
- no new broad autonomy claims
- any new failure should be handled through the compatibility/self-heal contracts added in 124–128
- docs/status updates must remain green-gated

## Acceptance
- orchestrator-run Task 129 reaches green without manual recovery patching
- focused and full validation are green
- docs/state/spec claims match the proven deterministic supervised scope exactly
