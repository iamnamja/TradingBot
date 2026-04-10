# Orchestrator Roadmap 157–161

## Theme

Single-task reliability sprint.

The first live proof-mode runs were valuable because they showed where the orchestrator still breaks down in real execution: helper-only partial completion, empty bundle transport failures, runtime artifact ambiguity, and incomplete integration coverage. This slice is explicitly about getting one-task autonomy to run well before resuming the broader proof roadmap.

## Why this slice exists

The project does not currently need more generic autonomy surfaces. It needs a short reliability sprint that improves one-task completion quality and reduces the gap between “passing local helper/tests” and “real task completion through the orchestrator.”

## Tasks

### 157 — benchmark scorecard integration
Wire strict no-manual-intervention scorecarding into the real benchmark/session artifact path.

### 158 — empty bundle transport retry and classifier
Treat empty bundle responses as a first-class transport failure family with explicit diagnostics and bounded retry behavior.

### 159 — runtime artifact quarantine and subset preservation normalization
Normalize proof-mode runtime artifacts so successful runs are easier to interpret and leftover files do not look mysterious.

### 160 — completion integrity gate
Reject helper-only partials for tasks that require integration into benchmark/session/runtime surfaces.

### 161 — one-task reliability minipack re-proof
Run a small curated reliability pack and decide whether the one-task lane is truly improving.

## Expected outcome

By the end of this slice, we should know one of two things honestly:

1. the orchestrator can now complete one-task proof-mode work much more reliably and the broader roadmap can resume, or
2. one-task autonomy is still too fragile and needs another focused reliability sprint before broader progress resumes.
