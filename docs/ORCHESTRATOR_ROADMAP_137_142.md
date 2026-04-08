# Orchestrator Roadmap 137–142

This tranche follows the bounded supervised resilience re-proof through Task 136.

The goal is **not** to jump directly to broad unattended autonomy. The goal is to create a narrow, operationally honest **safe autonomous single-task lane** that can run reliably before the orchestrator is trusted with broader self-hosting work.

## Why this tranche exists

Tasks 124–136 materially improved the orchestrator’s resilience, but the project is still showing two important realities:

- self-hosting control-plane tasks remain the hardest failure class and still often require manual correction
- hosted-authority truth is modeled and tested, but the real GitHub setup is not yet operationally converged enough to justify unattended claims

This tranche shifts from “more resilience vocabulary” toward “a lane that can actually run independently, one safe task at a time.”

## Tasks

### 137 — Real GitHub required-check / branch-protection convergence
Move from modeled hosted-authority truth to real operational convergence around the stable `ci-required` context, including explicit setup verification and clear blocking evidence when the repo is not truly unattended-ready.

### 138 — Safe task-family autonomy allowlist and admission lane
Add an explicit allowlist for autonomous single-task runs so the orchestrator can safely run ordinary implementation/test/doc tasks while self-hosting control-plane work remains escalation-first by default.

### 139 — Autonomous single-task runner and run ledger
Introduce a dedicated one-task autonomous runner plus a persisted run ledger capturing admission decision, branch, retries, validation outcome, escalation reason, and final stop/continue posture.

### 140 — Canary metrics and recovery reporting
Aggregate autonomous single-task run outcomes into durable canary metrics so the project can measure completion rate, repair convergence, stop reasons, and hosted-authority blocking frequency.

### 141 — Escalation artifact and supervised handoff lane
When a task falls outside the safe autonomy lane, emit a clean escalation artifact that explains why it was blocked, what files were implicated, and what the next supervised/manual action should be.

### 142 — Supervised safe-lane autonomous single-task re-proof
Re-prove the orchestrator over the new safe autonomy lane: allowlisted admission, single-task runner, run ledger, canary metrics, escalation artifacts, conservative stop posture, and real hosted-authority readiness truth.

## Intended execution posture

- 137–141: manual-first
- 142: orchestrator-supervised, one-task canary, bounded

## Desired outcome

By the end of this tranche, the project should be able to honestly say:

- the orchestrator can autonomously run **one safe ordinary task at a time**
- the system measures whether those runs are actually succeeding
- self-hosting control-plane work is explicitly escalated instead of failing ambiguously
- broader unattended autonomy still remains blocked until the safe lane proves reliable in practice
