# Orchestrator Roadmap — Backlog Execution and Controller Decomposition Continuation (069–075)

## Where this continuation starts

The 055–068 continuation and stabilization extension drove the orchestrator to a better place, but they also made the next gap obvious:

- ordinary tasks are more reliable
- explicit deliverable completeness is enforced
- protected/controller failures are now surfaced more truthfully
- duplicate-bundle recovery and the first controller extraction are underway

However, the orchestrator is **not yet at the point where it can confidently take a list of tasks and work through them end to end**.

This roadmap continues from that reality rather than pretending the backlog runner already exists.

## Current prerequisite state

Before starting this roadmap, the expected immediate sequence is:

- original **068** should be retried after the 068a–068c stabilization work
- then the continuation below begins at **069**

## Continuation goals

This tranche now has three linked goals:

1. keep making `agents/run_task.py` less monolithic
2. add the minimum viable backlog/list-execution model needed for the orchestrator to progress through multiple tasks automatically
3. make “green” mean the same thing as operator-observed merge readiness before exposing the first batch runner CLI

## Planned order

### 069 — Controller decomposition second extraction
Extract protected-lane coordination and bundle-repair helpers out of the controller so later backlog work is not piled onto one protected file.

### 070 — Task-list manifest and queue model
Add a deterministic manifest format and queue representation for a list of tasks.

### 070a — Exact deliverable parser and completion gate
Make exact required-file parsing and completion enforcement match the current backlog task format.

### 070b — Runtime artifact retention and visibility
Make runtime artifact lifecycle behavior visible and operator-controllable while preserving quarantine as the default.

### 071 — Batch state persistence and resume
Persist queue progress so a backlog run can resume rather than starting over.

### 071a — User-facing runtime artifact retention switch
Expose the runtime-artifact retention path through a supported env/CLI control.

### 072 — Per-task checkpoint and branch isolation
Record task-by-task isolation/checkpoint data so one task does not silently contaminate the next.

### 073 — Batch failure policy and continue gate
Add explicit continue/stop/manual decisions between queued tasks.

### 074a — Merge-ready validation profile
Require the orchestrator to run an authoritative local merge-ready validation profile before claiming success.

### 074b — Post-green validation retry loop
If the merge-ready validation profile fails after a nominal green pass, iterate and repair rather than silently stopping at a false green.

### 074c — Committed-state parity and unexpected-artifact gate
Require final success to match committed `HEAD` and reject unexpected tracked artifacts before completion.

### 074 — Batch runner CLI and summary artifacts
Expose a first user-facing way to execute a task list and review the results.

### 075 — Backlog execution end-to-end proof
Add a narrow but honest E2E proof that the orchestrator can move through a short manifest conservatively.

## Why this order

The backlog runner should not arrive first. If it arrives before the controller is further decomposed and before inter-task policy/state exist, it will simply make existing controller fragility more expensive.

Recent 069–073 work also showed a more specific gap: a task can appear green in the orchestrator loop while still not being fully merge-ready under the operator’s real post-run checks. The first batch runner CLI should not be introduced until that gap is narrowed.

This order therefore goes:

- controller thinning
- queue representation
- persisted batch state
- task isolation
- post-task continue gate
- merge-ready validation hardening (074a–074c)
- user-facing batch runner
- E2E proof

## Expected lane mix

- **Likely manual-patch / controller-touching tasks**
  - 069
  - 074a
  - 074b
  - 074c
- **Expected autonomous lane once the hardening tasks land**
  - 070
  - 071
  - 072
  - 073
  - 074
  - 075

## Success criteria for this roadmap

This roadmap is successful when:

- `agents/run_task.py` is materially thinner than it was at the start of 069
- the orchestrator can parse and persist a task-list manifest
- “green” inside the orchestrator means the same thing as operator-observed merge readiness
- the batch runner can progress through a short manifest conservatively
- state, summaries, and stop/continue decisions are explicit and test-backed
- the project can honestly say it has a first backlog-execution proof, not just a collection of single-task capabilities
