# Orchestrator Reliability / Recovery / Autonomy Review

## Why this review exists

The orchestrator has become strong enough to enforce guardrails, but not yet strong enough to behave like a reliable central command system across a long backlog.

The current bottleneck is no longer only “can the harness recover from failures.” It is also whether the safe one-task lane is operationally trustworthy on live GitHub branches.

## Current strengths

- shell-routed execution and worktree/branch guardrails are present
- protected-file policies exist
- spec/frozen-task support exists
- validator and failure-journal seams exist
- bundle preflight and localized repair support exist
- portability/adapters groundwork is already in place
- the repo now has a bounded one-task autonomous lane with ledger, canary reporting, and supervised handoff artifacts

## Current weaknesses

### 1. Live hosted-authority interpretation still needs hardening
The repo should treat GitHub reporting races, check-run vs commit-status surfaces, and real required-check convergence more explicitly.

### 2. The safe lane still needs deeper scheduler integration
The bounded single-task runner exists, but the scheduler should route through it directly when exactly one safe task is ready.

### 3. Mixed queues need cleaner conservative handling
The system must stop or requeue cleanly when safe work and supervised-only work appear together.

### 4. Resume semantics for the safe lane are still a maturity gap
Interrupted one-task runs should be resumable without artifact duplication or widened scope.

### 5. Operator proof needs to be more explicit
A small live canary proof bundle should make it easy to see what the lane can do and what it still refuses to do.

## Do we need AI on top?

No separate AI supervisor should sit above the orchestrator.

What we need instead is an **embedded controller-intelligence layer** inside the orchestrator itself. That layer should be allowed to use models, but only within explicit policy, confidence, and contract boundaries.

Its responsibilities should include:

- task-family classification
- lane-specific prompt/request compilation
- seam manifest and semantic contract validation
- failure classification and remediation planning
- confidence-gated autonomy vs escalation decisions
- hosted-authority interpretation across live GitHub surfaces

## Design target

The orchestrator should behave like this:

1. Read backlog state and identify ready tasks.
2. Classify the next task family.
3. Compile the correct request for the lane.
4. Run generation and validation.
5. Classify any failure.
6. Repair locally when safe.
7. Escalate to manual patch lane when needed.
8. Interpret live PR authority conservatively.
9. Merge only when the required contract is truly green.
10. Mark the task done and advance to the next ready task.

## Immediate build priorities

1. settle-window and dual-surface hosted-authority probe
2. real-PR `ci-required` smoke proof
3. scheduler bridge to the bounded single-task runner
4. mixed-queue stop/requeue discipline
5. one-task resume and idempotent re-entry
6. live canary proof bundle
