# Orchestrator Product Spec

## Purpose

The orchestrator is evolving from a guarded task runner into a **central software-delivery control plane** that can:

- understand backlog state and readiness
- select the next task autonomously
- choose the correct execution lane for the task family
- compile the right prompt/request for that lane
- run generation, validation, repair, PR, CI, and merge loops safely
- record deterministic audit artifacts and recovery history
- stay portable across projects through adapters and constrained seams

## Product posture

The orchestrator is still co-located in this repository and is not yet extracted into its own repo/package.

The immediate goal is not more breadth of capability. The immediate goal is **reliable autonomous behavior across task families**.

## Current strengths

The current baseline already includes:

- shell-routed execution and guardrails
- protected-file policy enforcement
- spec-mode / frozen-task support
- validator integration and deterministic result handling
- failure journal and runtime artifact seams
- portability/adapters groundwork
- initial seam-aware preflight and localized repair support

## Current gap

The orchestrator still lacks a sufficiently reliable control plane. In practice, narrow tasks still take too many manual iterations because the system does not yet consistently:

- classify task families correctly
- compile the best lane-specific request
- validate seam contracts semantically instead of only with string heuristics
- decide when to retry, repair locally, split, defer, or escalate
- keep good files and repair only bad files
- choose the next ready task on its own
- run a safe PR/CI/merge loop as a first-class workflow

## Do we need AI on top?

No separate AI supervisor is required.

What is required is an **embedded controller-intelligence layer** inside the orchestrator. It should be model-assisted but policy-constrained. Its responsibilities should include:

- task-family classification
- prompt/request compilation per lane
- seam-manifest / contract validation
- failure classification and remediation planning
- confidence-gated autonomy vs escalation decisions

This keeps the orchestrator as the control plane while making reasoning a governed internal subsystem rather than an uncontrolled layer sitting on top.

## New active tranche: Reliability / Recovery / Autonomy (055–061)

### 055 / 055a / 055b / 055c — umbrella, contract freeze, task-family prompt compiler, seam manifest validator
Stabilize the harness contract, teach the controller how to distinguish task families, compile better lane-specific requests, and validate live seam contracts semantically.

### 056 — failure classifier + remediation planner
Turn failed executions into structured decisions such as retry, local repair, task-shape patch, runner patch, manual patch lane, or blocked/waiting.

### 057 — localized repair + failure artifacts
Guarantee that small task failures preserve valid outputs, repair only the bad subset, and always emit usable failure artifacts.

### 058 — backlog readiness + state engine
Track task status, readiness, blockers, dependencies, and human/manual-lane state so the controller can know what is ready next.

### 059 — CI / PR / merge controller
Promote PR creation, CI polling/classification, merge, resync, and next-task unlocking into first-class orchestrator behavior.

### 060 — autonomy loop integration
Run the above pieces together as one central-command loop over a backlog and prove that it can self-heal through at least one recoverable failure without human intervention.

### 061 — continuation reset and numbering sync
Realign docs, backlog numbering, and continuation language so the deferred tranche resumes on a clean foundation.

## Deferred continuation after reliability tranche

- 062 integrated capability E2E flow
- 063 failure-journal live seam
- 064 safe parallelism / review integration
- 065 runtime artifact quarantine integration
- 066 package extraction prep
- 067 canonical docs path policy
- 068 task scope / split heuristics follow-on
