# Orchestrator Roadmap 143–148

This tranche follows the bounded supervised safe-lane re-proof through Task 142.

The goal is still **not** to jump directly to broad unattended autonomy. The goal is to make the existing one-task safe lane operationally trustworthy on real GitHub branches and then route the scheduler through that bounded lane honestly.

## Why this tranche exists

Tasks 137–142 created the narrow safe autonomous one-task lane, but two realities remain:

- the repo still needs stronger operational interpretation of live GitHub reporting and required-check timing
- the bounded single-task runner exists, but the orchestrator scheduler should use it more directly before broader claims are made

This tranche turns the safe lane from “proved in bounded form” into “operationally trustworthy enough to use under supervision.”

## Tasks

### 143 — GitHub settle window and dual-surface probe
Treat live GitHub authority more realistically by reading both check-run and commit-status surfaces and by distinguishing initial reporting delay from genuinely missing required-check evidence.

### 144 — Real PR required-check smoke proof
Add a small supervised smoke proof on an open PR that records whether `ci-required` really appears and really blocks merge until green.

### 145 — Scheduler bridge to safe single-task runner
Route the orchestrator’s single-ready-safe-task path through the dedicated bounded runner so the safe lane becomes the scheduler’s canonical one-task execution surface.

### 146 — Safe-lane stop, requeue, and supervised mix policy
Handle mixed queues conservatively: run at most one safe task, emit explicit supervised handoff for blocked work, requeue what remains, and stop cleanly.

### 147 — Single-task resume and idempotent re-entry
Make bounded one-task runs safe to resume after interruption without duplicating ledger rows, handoff artifacts, or execution scope.

### 148 — Live canary corpus and operator proof bundle
Package the bounded lane into an operator-readable proof bundle with one safe task, real hosted-authority evidence, durable artifacts, and explicit escalation for out-of-lane work.

## Intended execution posture

- 143–144: manual-first, live-GitHub supervised
- 145–147: bounded orchestrator-supervised implementation
- 148: supervised canary proof bundle

## Desired outcome

By the end of this tranche, the project should be able to honestly say:

- live GitHub `ci-required` behavior is interpreted conservatively and correctly
- the orchestrator scheduler can route exactly one safe task through the bounded runner
- mixed queues stop and hand off conservatively instead of widening autonomy
- one-task runs can safely resume without corrupting artifacts
- operators have a small proof bundle that shows what the lane can do and what it still refuses to do
