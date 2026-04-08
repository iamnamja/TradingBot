# Task 134 — Orchestrator last-green subset preservation and rollback

## Goal
Preserve the last-known-good file subset during retries so targeted repairs stop re-breaking files that were already good.

## Scope
- accepted parsed bundle subset
- localized repair / retry cycles
- rollback boundary limited to the failing subset

## Required changes
- persist the last-known-good subset for the current task attempt
- roll back only the failing subset before targeted repair
- expose the preserved/rolled-back subset through stable artifacts for debugging
- keep the behavior bounded and deterministic

## Acceptance
- focused tests prove good files are preserved while only failing files are rolled back
- repeated retries on the same task do not unnecessarily widen the changed-file set
- full validation stays green
