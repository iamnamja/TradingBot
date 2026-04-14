# Task 178 — orchestrator supervised intervention artifact and pilot failure digest

## Why

The bounded pilot is supervised. That means the repo must record supervision truth explicitly so operator help never gets mistaken for autonomous success. It also needs a pilot-specific failure digest that is richer than generic failure buckets.

## Scope

Persist supervised-intervention truth and a bounded pilot failure digest for two-task pilot runs.

## Runtime seams to reuse

- Reuse pair/session ledgers from Task 176.
- Reuse the canary vocabulary from Tasks 174–175:
  - blocked admission,
  - handoff incomplete,
  - handoff incompatible,
  - supervised intervention.
- Reuse one-task scorecard honesty rules where human intervention invalidates autonomous claims.

## Requirements

- Write a durable supervised-intervention artifact or ledger extension that records:
  - where supervision occurred,
  - why it occurred,
  - whether it invalidated autonomous progress for the pair,
  - whether the pilot still completed under supervision.
- Write a pilot failure digest that can distinguish at minimum:
  - admission blocked,
  - handoff incomplete,
  - handoff incompatible,
  - controller override,
  - manual stop,
  - runtime failure.
- Ensure human/operator intervention is never misreported as autonomous success.
- Keep this additive to the existing one-task scorecard and two-task canary truth.

## Non-goals

- Do not widen into a general incident-management system.
- Do not rewrite the already-proven one-task scorecard surfaces.

## Acceptance criteria

- Tests prove supervised intervention is persisted durably and explicitly.
- Tests prove bounded pilot failures are classified into specific digest buckets.
- Tests prove autonomous claims remain conservative when supervision occurs.
