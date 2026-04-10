# Orchestrator Roadmap 149–154

This tranche follows the bounded one-task proof bundle through Task 148.

The goal is **not** to jump straight to bounded multi-task autonomy or to build a separate app shell. The goal is to make the existing one-task lane complete ordinary external-style safe tasks with a measurable pass rate and targeted self-heal behavior.

## Why this tranche exists

Tasks 137–148 created the narrow one-task autonomous lane and proved it in bounded operator-readable form. That was the right stabilization step, but it still leaves a practical problem:

- the orchestrator still needs too much manual patching on ordinary runs
- the project needs measured execution quality, not more orchestration surface area
- multi-task widening and self-hosting should not happen until the one-task lane has earned them

This tranche turns the current lane from “bounded and honest” into “measurably useful on ordinary external-safe work.”

## Tasks

### 149 — External-safe corpus and evaluation manifest
Define the canonical external-safe one-task corpus and the archetype metadata that later tasks will use for measurement and re-proof.

### 150 — One-task multi-agent dev / test / repair loop
Make a bounded one-task run behave like a real role-separated execution loop instead of just a generation shell with validation tacked on.

### 151 — External-safe failure taxonomy and self-heal router
Classify the most common ordinary one-task failures and route them into the smallest credible repair lane.

### 152 — One-task pass-rate scoreboard and failure digest
Measure completion rate, retry rate, escalation rate, and dominant failure classes across the external-safe corpus.

### 153 — External-safe corpus reliability re-proof
Re-prove the current one-task claim against measured external-safe execution quality instead of only against proof-shaped canaries.

### 154 — Two-task readiness gate and phase transition
Define the explicit go / no-go gate for bounded two-task trials so widening depends on evidence, not on optimism.

## Intended execution posture

- 149–152: bounded supervised implementation and measurement
- 153: supervised reliability re-proof
- 154: evidence-based phase gate only

## Desired outcome

By the end of this tranche, the project should be able to honestly say:

- the orchestrator has a canonical external-safe one-task proving ground
- one-task runs use a real dev / test / repair / controller loop
- targeted self-heal is improving ordinary completion quality
- operators can see the real pass-rate and top failure classes
- the project knows whether it has earned the right to attempt bounded two-task trials
