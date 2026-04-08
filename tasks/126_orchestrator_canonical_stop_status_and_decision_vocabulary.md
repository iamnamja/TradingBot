# Task 126 — Orchestrator canonical stop-status and decision vocabulary

## Goal
Unify stop/blocked/manual-patch/merge-failure vocabulary across controller contract, batch state, batch executor, and merge helpers.

## Scope
- batch status values
- post-task decisions
- acceptance decisions
- merge posture failure decisions

## Required changes
- create one canonical mapping layer for vocabulary coercion
- make near-synonyms resolve to the canonical public/tested values
- add focused tests for vocabulary normalization and persisted truth

## Acceptance
- controller/batch/merge tests no longer depend on scattered string literals
- manual patch and blocked posture remain conservative and explicit
- full `ruff check .` and `pytest -q` are green
