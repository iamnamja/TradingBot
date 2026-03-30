# Orchestrator Roadmap — Backlog Execution and Controller Decomposition Continuation (069–075 + 070a/070b)

## Where this continuation starts

The 055–070 continuation moved the orchestrator into real backlog-execution groundwork, but it also exposed two immediate trust/visibility gaps:

- exact markdown deliverables can still be omitted from otherwise green runs unless operators verify the branch diff manually
- runtime scratch artifacts such as `_last_agent_model_output.txt` and `_last_agent_file_bundle.txt` are intentionally quarantined on successful push paths, but the operator experience remains confusing and offers no explicit retention control

That means the next continuation step is not to rush into state persistence. The controller first needs a tighter exact-deliverable gate and clearer runtime-artifact lifecycle controls.

## Current prerequisite state

Before resuming the broader backlog-execution tranche, the expected sequence is now:

- **068** confirmed after the 068a–068c stabilization work
- **069** landed to continue controller decomposition
- **070** landed task-list manifest and deterministic queue groundwork
- **070a** and **070b** now harden the controller contract and artifact lifecycle before **071**

## Continuation goals

This tranche now has three linked goals:

1. keep making `agents/run_task.py` less monolithic and more trustworthy
2. make exact deliverable completion align with the current task-contract style
3. continue adding the minimum viable backlog/list-execution model needed for the orchestrator to progress through multiple tasks automatically

## Planned order

### 069 — Controller decomposition second extraction
Extract protected-lane coordination and bundle-repair helpers out of the controller so later backlog work is not piled onto one protected file.

### 070 — Task-list manifest and queue model
Add a deterministic manifest format and queue representation for a list of tasks.

### 070a — Exact deliverable parser and completion gate hardening
Broaden exact-file parsing so canonical `docs/`, `tasks/`, and explicit top-level files can be enforced by the controller instead of only by operator diff review.

### 070b — Runtime artifact retention and visibility controls
Keep runtime-artifact quarantine by default, but add explicit controls and clearer lifecycle messaging for retaining known-safe scratch artifacts during debugging.

### 071 — Batch state persistence and resume
Persist queue progress so a backlog run can resume rather than starting over.

### 072 — Per-task checkpoint and branch isolation
Record task-by-task isolation/checkpoint data so one task does not silently contaminate the next.

### 073 — Batch failure policy and continue gate
Add explicit continue/stop/manual decisions between queued tasks.

### 074 — Batch runner CLI and summary artifacts
Expose a first user-facing way to execute a task list and review the results.

### 075 — Backlog execution end-to-end proof
Add a narrow but honest E2E proof that the orchestrator can move through a short manifest conservatively.

## Why this order

The backlog runner should not arrive first. If it arrives before the controller is further decomposed and before inter-task policy/state exist, it will simply make existing controller fragility more expensive.

That logic now has an extra prerequisite layer:

- exact-file completion must fail closed for canonical markdown deliverables
- runtime artifact behavior must be easier to reason about during debugging
- only then should queue persistence and batch execution continue to grow

This order therefore goes:

- controller thinning and queue groundwork
- exact deliverable gate hardening
- runtime artifact lifecycle controls
- persisted batch state
- task isolation
- post-task continue gate
- user-facing batch runner
- E2E proof

## Expected lane mix

- **Likely manual-patch / controller-trust tasks**
  - 070a
- **Reasonable autonomous candidates once 070a lands**
  - 070b
  - 071
  - 072
  - 073
  - 074
  - 075

## Success criteria for this roadmap

This roadmap is successful when:

- `agents/run_task.py` is materially thinner and more trustworthy than it was at the start of 069
- exact-file deliverables fail closed when omitted, including canonical docs/tasks paths
- operators can intentionally retain known-safe runtime scratch artifacts without those artifacts slipping into commits
- the orchestrator can parse and persist a task-list manifest
- the batch runner can progress through a short manifest conservatively
- state, summaries, and stop/continue decisions are explicit and test-backed
- the project can honestly say it has a first backlog-execution proof, not just a collection of single-task capabilities
