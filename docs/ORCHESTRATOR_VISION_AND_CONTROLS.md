# Orchestrator Vision and Controls

## Vision

Create a reusable orchestration product that operates as a **central command system** for software delivery: it should understand backlog state, choose the next ready task, execute the right workflow for that task family, validate outputs, repair what is salvageable, escalate when needed, and advance the backlog with strong auditability.

## Productization stance (current)

- reusable and increasingly productized
- still co-located in this repository
- not yet extracted into a standalone repository/package

## Maturity checkpoint

- 042–048 hardening tranche: **complete**
- 049–054 continuation hardening tranche: **complete**
- 055–061 reliability / recovery / autonomy tranche: **active next priority**
- 062–068 deferred continuation: **paused until reliability tranche lands**

## Control principles

1. **Explicit contracts over implicit behavior**
2. **Safety-by-default over convenience-by-default**
3. **Deterministic execution summaries and failure artifacts**
4. **Recoverable workflows with persistent state**
5. **Auditability and reviewability at each decision point**
6. **Portable architecture via adapters and constrained interfaces**
7. **Task-family awareness before code generation**
8. **Localized repair before whole-task restart**
9. **Semantic seam validation before permissive retries**
10. **Autonomous control-plane behavior before broad integration claims**
11. **Embedded controller intelligence, not an uncontrolled AI layer on top**

## Near-term strategy (055–061)

- freeze the stable harness contract
- classify task families and compile lane-specific requests deliberately
- maintain a seam manifest and semantic contract validator
- classify failure modes and map them to remediation plans
- guarantee localized repair and durable failure artifacts
- maintain backlog readiness state and next-task selection
- integrate PR/CI/merge into the orchestrator’s control loop
- realign numbering/docs so the deferred continuation can resume cleanly afterward

## Separation recommendation

Perform repository/package separation later, after the reliability/autonomy tranche and the deferred continuation demonstrate stable autonomous behavior rather than only stable shell/test seams.
