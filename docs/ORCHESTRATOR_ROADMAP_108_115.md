# Orchestrator Roadmap — Autonomy Operating-Mode Continuation (108–115)

## Where this continuation starts

Task 107 completed a bounded supervised mixed-manifest local-first re-proof.

That is a useful milestone, but recent recovery work also showed that the orchestrator still behaves more like a **proof-backed engine** than a durable operating mode for broader autonomous ordinary-task work.

The next tranche should therefore focus on turning the current proof slice into a more stable execution mode.

## Main gaps this tranche addresses

- coder/tester/controller role handoffs are still too loosely shaped and too easy to regress
- tester/verifier evidence is still too close to raw pytest output instead of focused critique bundles and replay instructions
- self-heal still lacks durable memory against repeated no-progress repair attempts
- broader task shapes still need clearer admission and decomposition gates before safe autonomous execution
- hosted CI authority remains truthful in code but not yet durable enough in live repo behavior
- the current multi-agent loop is still more proof-facing than ordinary-task execution-facing
- cross-task carry-forward memory is too weak for less-babysat backlog progression

## Planned order

### 108 — Role handoff artifact envelopes and persistence
Stabilize coder/tester/controller artifact envelopes and persist them explicitly in batch state and failure-journal surfaces.

### 109 — Tester critique bundle and focused replay lane
Teach the tester/verifier lane to emit focused critique bundles, candidate replay commands, and bounded evidence instead of only raw red-test blobs.

### 110 — Repair memory and duplicate-attempt suppression
Persist repair fingerprints and edited-file surfaces so no-progress repair loops stop repeating the same patch shape.

### 111 — Task admission and decomposition gate
Add safe task-family admission, supervised/manual gating, and bounded decomposition for larger or ambiguous task shapes.

### 112 — Repo check contract and hosted-authority probe
Move the hosted-check story from only truth modeling toward a repo-scoped contract and stronger probe behavior around real required checks.

### 113 — Multi-role ordinary-task execution loop
Convert the current proof-facing role loop into a stronger ordinary-task execution surface with explicit builder/tester/controller coordination.

### 114 — Cross-task context carry-forward and repo memory
Let the orchestrator carry accepted changes, unresolved issues, deferred blockers, and bounded repo memory forward across tasks.

### 115 — Supervised end-to-end ordinary-manifest autonomy re-proof
Re-prove the orchestrator over a short ordinary manifest that uses the stronger multi-role/task-memory surfaces while remaining supervised and local-first.

## Expected lane mix

- **Manual first:** 108, 109, 110, 111, 112, 113
- **Manual or hybrid:** 114
- **Best orchestrator candidate after those land:** 115

## Success criteria for this roadmap

This roadmap is successful when:

- role handoff envelopes stay stable across adjacent controller work
- tester evidence becomes more focused and actionable
- repair loops stop repeating no-progress patches
- larger tasks are admitted or decomposed more honestly
- hosted authority remains truthful in live repo behavior, not only in local semantics
- the orchestrator can execute a short ordinary manifest with less babysitting than today
- a new supervised end-to-end autonomy re-proof succeeds after those hardenings land
