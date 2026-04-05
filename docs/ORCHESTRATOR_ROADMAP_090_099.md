# Orchestrator Roadmap — Multi-Agent Portability and Productization (090–099)

## Where this continuation starts

Task 089 completed the hardened short ordinary-manifest proof.

That was the right time to stop hardening only the controller contract and ask what the product still needs in order to become a stronger project builder.

The biggest remaining gaps are now:

- no canonical multi-agent role contract
- no explicit builder/verifier/controller loop
- verification authority still needs stronger CI-backed truth
- repair strategy selection is still less explicit than the new semantic digest deserves
- project/workspace portability is not yet a strong proof surface
- ordered manifests still need dependency-aware planning
- the orchestrator product boundary is clearer, but not yet strong enough for standalone packaging claims

## Continuation goals

This tranche has seven linked goals:

1. define one canonical multi-agent role contract with persisted handoff truth
2. implement a sequential builder/verifier/controller loop
3. make verification authority and required CI checks first-class controller evidence
4. add an explicit repair-strategy router and role-aware remediation selection
5. strengthen project/workspace portability and bootstrap contracts
6. move from ordered-only manifests to dependency-aware planning and task-family routing
7. prove the orchestrator against a second Python project shape and tighten the product boundary for later extraction

## Planned order

### 090 — Multi-agent role contract and handoff state
Create one importable three-role contract and persist controller/builder/verifier handoff truth.

### 091 — Builder/verifier/controller loop
Implement a canonical sequential role-separated execution loop while preserving controller authority.

### 092 — Verification authority and CI required checks
Make local vs CI-required verification posture explicit and persisted before merge decisions.

### 093 — Repair strategy router and failure-lane selection
Turn semantic failure digests into explicit remediation lanes rather than one generic retry surface.

### 094 — Project workspace adapter and bootstrap contract v2
Strengthen the reusable project/workspace contract so the orchestrator can reason over external project setup and validation.

### 095 — Dependency-aware manifest planner
Let the orchestrator reason over prerequisites, blocked tasks, and honest defer/reorder behavior.

### 096 — Task-family router and agent selection
Choose the next role/lane based on task family and failure posture, while keeping controller authority and strict-mode limits.

### 097 — Second-project multi-agent portability proof
Prove the multi-agent controller architecture over a simple external Python project shape.

### 098 — Standalone package boundary and consumer bridge
Clarify the orchestrator’s reusable product boundary and TradingBot’s role as one consumer, without claiming full extraction yet.

### 099 — Multi-agent portability proof sync
Synchronize the stronger proof slice across tests/docs once the above contracts and proofs are green.

## Expected lane mix

- **Likely manual-patch / controller-core / harness-core tasks**
  - 090
  - 091
  - 092
  - 093
  - 094
  - 095
  - 096
  - 098
- **Best autonomous/proof candidates after those contracts land**
  - 097
  - 099

## Working assumptions for this roadmap

This roadmap intentionally assumes:

- Python-first portability before any multi-language claim
- sequential role separation before any real parallel multi-agent scheduling
- controller remains the sole authority that chooses the next role/lane
- CI-required checks should become a first-class merge authority
- the orchestrator remains in the current monorepo for this tranche, but the product boundary should be strengthened for later extraction

## Success criteria for this roadmap

This roadmap is successful when:

- the repo has one canonical builder/verifier/controller contract
- role handoffs are persisted and auditable
- verifier/CI evidence becomes first-class controller truth
- repair routing becomes strategy-aware instead of generic
- external project bootstrap/validation can be described through one reusable workspace adapter
- manifests can represent dependencies and blocked tasks honestly
- a simple second Python project proves the portability slice
- the orchestrator’s reusable boundary is strong enough that TradingBot is clearly a consumer, not the product identity

## “Can I feed it a whole project backlog yet?” posture after this tranche

After 089: yes for a **short ordinary-manifest proof slice** in the current bounded posture.

After 090–099, the goal is to be able to say:

- a controller can choose between builder, verifier, and constrained/manual lanes more explicitly
- a short Python project backlog with dependencies can be run more credibly across more than one project shape
- merge authority and repair selection are stronger and more trustworthy
- the orchestrator is closer to a standalone product boundary, but still not a claim of arbitrary any-language unattended app creation
