# Orchestrator Roadmap 181–185

## Tranche theme

Reliability first, capability next.

The repo has completed the bounded supervised two-task pilot proof surfaces through Task 180. The next tranche should not widen capability yet. It should reduce recurring orchestration failures that still show up in real task runs.

## Why this slice exists

Recent work showed a repeated pattern:

- a task can be directionally correct but still fail because a shared compatibility surface drifted,
- benchmark and runner work can accidentally touch the wrong public contract if the guardrails are not explicit enough,
- proof-task admission and exact deliverable contracts can still block runs before model execution,
- recovery and retry logic still sometimes spend effort on framework discipline instead of the task’s real code goal.

This slice addresses those reliability bottlenecks directly.

## Task plan

### Task 181 — orchestrator failure family taxonomy and repair target selection

Create a durable taxonomy for the most common orchestrator failure families and wire narrow repair-target selection to that taxonomy.

Focus:
- task admission / exact deliverable contract failures,
- import/public compatibility failures,
- artifact-path and artifact-shape mismatches,
- benchmark compatibility regressions,
- static-contract / protected-surface failures,
- environment / runner-entrypoint mismatches.

Goal:
- reduce broad repair attempts and increase correct first repair target selection.

### Task 182 — orchestrator import contract and additive compatibility guardrails

Harden the public/import compatibility surfaces that recent work has stressed.

Focus:
- additive benchmark extensions,
- bounded pilot runner entrypoints,
- compatibility aliases that tests and docs depend on,
- explicit guarantees that one-task truth surfaces remain untouched by two-task reliability work.

Goal:
- make benchmark and runner changes safer and less likely to regress shared surfaces.

### Task 183 — orchestrator resume checkpoint and attempt state re-entry

Persist resume-safe attempt checkpoints and recovery truth so partially-successful runs can re-enter precisely.

Focus:
- attempt metadata,
- checkpoint transition state,
- last-safe subset / resume intent truth,
- clear differentiation between fresh execution, resume, retry, and manual intervention.

Goal:
- reduce repeated broad retries after partial progress.

### Task 184 — orchestrator reliability benchmark and regression matrix

Measure the runtime more directly.

Focus:
- one-task and bounded two-task runs,
- retry count to green,
- supervision rate,
- recurring failure families,
- compatibility regression frequency,
- admission-block frequency.

Goal:
- turn reliability into a measurable gate instead of a vague impression.

### Task 185 — orchestrator reliability checkpoint and capability gate

Record an explicit checkpoint after the reliability tranche.

Focus:
- whether recurring failure families have been reduced materially,
- whether resume-safe recovery is working,
- whether compatibility regressions are rarer,
- whether capability widening may resume,
- what remains blocked.

Goal:
- do not reopen capability widening on intuition alone.

## Non-goals for this slice

- no broad unattended multi-task autonomy claim,
- no standalone app extraction claim,
- no arbitrary dynamic role orchestration,
- no unbounded task-sequence scheduling,
- no capability widening unless the reliability checkpoint explicitly supports it.
