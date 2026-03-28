# Orchestrator Reliability / Recovery / Autonomy Review

## Why this review exists

The orchestrator has become strong enough to enforce guardrails, but not yet strong enough to behave like a reliable central command system across a long backlog.

The repeated 20–30 turn repair cycles on narrow tasks are evidence that the current bottleneck is not only model quality or task wording. The deeper issue is that the orchestrator still lacks a mature control plane.

## Current strengths

- shell-routed execution and worktree/branch guardrails are present
- protected-file policies exist
- spec/frozen-task support exists
- validator and failure-journal seams exist
- bundle preflight and some localized repair support exist
- portability/adapters groundwork is already in place

## Current weaknesses

### 1. Task-family blindness
The runner still treats too many tasks as generic code generation problems.

### 2. Failure handling is reactive, not strategic
The system blocks bad output, but does not yet reliably decide whether a failure means retry, local repair, task patch, harness patch, manual patch lane, or stop.

### 3. Localized repair is not yet the default small-task behavior
Good files are not consistently preserved while bad subsets are repaired.

### 4. Backlog readiness is not a first-class controller concept
The system can run a task, but it does not yet own readiness, blockers, next-task selection, or long-loop autonomy.

### 5. PR/CI/merge behavior is still a workflow around the orchestrator, not inside it
A true central-command product needs PR/CI/merge status and failure interpretation as native controller behavior.

### 6. Semantic seam validation is too weak
The current harness still leans too hard on string/regex checks where seam-heavy tasks need manifest-driven or semantic validation.

### 7. Docs/task numbering drift still costs trust
Trajectory changes have repeatedly required manual renumbering and doc cleanup.

## Do we need AI on top?

No separate AI supervisor should sit above the orchestrator.

What we need instead is an **embedded controller-intelligence layer** inside the orchestrator itself. That layer should be allowed to use models, but only within explicit policy, confidence, and contract boundaries.

Its responsibilities should include:

- task-family classification
- lane-specific prompt/request compilation
- seam manifest and semantic contract validation
- failure classification and remediation planning
- confidence-gated autonomy vs escalation decisions

## Design target

The orchestrator should behave like this:

1. Read backlog state and identify ready tasks.
2. Classify the next task family.
3. Compile the correct request for the lane.
4. Run generation and validation.
5. Classify any failure.
6. Repair locally when safe.
7. Escalate to manual patch lane when needed.
8. Open PR, watch CI, merge, resync `main`.
9. Mark the task done and advance to the next ready task.

## Immediate build priorities

1. stable harness contract freeze
2. task-family classification and prompt compiler
3. seam manifest and semantic contract validator
4. failure classifier and remediation planner
5. localized repair and real failure artifacts
6. backlog readiness + state engine
7. PR/CI/merge controller
8. end-to-end autonomy loop integration
