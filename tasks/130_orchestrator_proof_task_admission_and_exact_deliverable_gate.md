# Task 130 — Orchestrator proof-task admission and exact-deliverable gate

## Goal
Prevent proof/re-proof tasks from reaching the model unless the task contract is concrete enough to support a deterministic expected-output surface.

## Scope
- proof, re-proof, portfolio-proof, and controller-proof task shapes
- exact repo-relative deliverable parsing
- admission-time rejection before model invocation when the contract is under-specified

## Required changes
- define one canonical admission rule for proof-style tasks
- require an explicit `Create or update these exact files` contract for proof-style tasks
- surface a narrow actionable admission error when the contract is missing or ambiguous
- make the admission result available through stable runtime exports and failure artifacts

## Acceptance
- proof-style tasks without exact deliverables are rejected before model execution
- focused tests cover allowed and blocked proof-task shapes
- no broader autonomy claim is added
