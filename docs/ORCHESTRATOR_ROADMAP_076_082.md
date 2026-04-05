# Orchestrator Roadmap — Autonomous Backlog Progression and Controller-Thinning Continuation (076–082)

## Where this continuation starts

069–075 established the first conservative backlog runner surfaces:

- task-list manifest and queue model
- persisted batch state and resume
- per-task checkpointing and continue gate
- merge-ready validation hardening
- first conservative batch runner CLI
- first narrow short-manifest end-to-end proof

That is meaningful progress, but it is still a **proof slice**, not yet the point where the orchestrator should be trusted to chew through an arbitrary list of tasks and merge everything on its own. The next tranche is about closing that gap honestly.

## What still needs to happen

The remaining gaps after 075 are now clearer:

- final acceptance review still needs a clean dedicated surface
- retryable acceptance failures still need more focused self-heal behavior
- batch execution logic should be a first-class controller loop, not just proof-oriented stitching
- accepted tasks still need a safe PR/create/check/merge/reset lifecycle before progression
- resume behavior after merge or manual resolution must be explicit
- `agents/run_task.py` still owns too much orchestration flow
- the project still lacks an honest proof of autonomous backlog progression across accepted tasks

## Continuation goals

This next tranche has four linked goals:

1. make final acceptance review explicit and reusable
2. make accepted-task self-heal + merge/reset progression real, not just manual operator choreography
3. continue thinning `agents/run_task.py` now that backlog execution is no longer just theoretical
4. establish a narrow, honest proof of autonomous backlog progression for ordinary tasks

## Planned order

### 076 — Final acceptance reviewer and report
Create a dedicated final-acceptance reviewer that compares task contract, committed `HEAD`, authoritative validation profile, and unexpected tracked artifacts.

### 077 — Targeted self-heal for acceptance failures
Classify final-acceptance failures into retryable/manual/blocked categories and generate focused repair prompts for retryable cases.

### 078 — Batch executor loop and acceptance controller
Turn sequential manifest execution into a dedicated controller loop that runs acceptance review and retry logic between tasks.

### 079 — Autonomous PR/merge and main-reset gate
Allow accepted tasks to go through PR/create/check/merge/reset main before the next task proceeds.

### 080 — Batch resume after merge and manual resolution
Resume cleanly after already-merged accepted tasks or after manual/blocking intervention is resolved.

### 081 — Controller decomposition third extraction
Move the new acceptance, batch-executor, and git-workflow controller logic further out of `agents/run_task.py`.

### 082 — Autonomous backlog runner proof
Add a narrow proof that a short ordinary-task manifest can self-heal, pass final acceptance, merge/reset, continue, and stop honestly on non-autonomous cases.

## Why this order

075 proved that conservative sequential backlog execution exists. The next bottleneck is not “can a manifest run at all?” but “can it run, self-correct, verify, merge, continue, and stop honestly without manual bookkeeping?”

That means the order must go:

- final acceptance surface
- retryable acceptance self-heal
- explicit batch executor loop
- accepted-task merge/reset lifecycle
- resume semantics
- further controller thinning
- honest autonomous backlog proof

## Expected lane mix

- **Likely manual-patch / controller-touching tasks**
  - 076
  - 077
  - 078
  - 079
  - 081
- **Good autonomous candidates once the new controller surfaces land**
  - 080
  - 082

## Success criteria for this roadmap

This roadmap is successful when:

- final acceptance review is explicit and reusable
- retryable acceptance failures can self-heal within bounded limits
- a batch executor/controller loop owns sequential manifest progression
- accepted tasks can PR/check/merge/reset before next-task continuation
- resume-after-merge and resume-after-manual-resolution are explicit
- `agents/run_task.py` is materially thinner again
- the project can honestly claim a first autonomous backlog-runner proof for a short manifest of ordinary tasks

## “Can I feed it a list yet?” posture

After 075: **not yet for arbitrary unattended lists**.  
After 078–080: reasonable to try a short list of ordinary, non-protected tasks under close review.  
After 082: reasonable to treat a short ordinary-task manifest as an honest autonomous proof slice, while still keeping protected/controller tasks in a conservative/manual posture.
