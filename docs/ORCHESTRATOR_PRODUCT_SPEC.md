# Orchestrator Product Spec

## Product goal

Build a reusable orchestration engine that can execute constrained implementation tasks safely across projects, with explicit policy controls, auditability, resumability, deterministic result handling, seam-aware testability, and role-separated execution.

## Current product stage

- Tasks 137–155 created and hardened the bounded autonomous one-task lane and its measurement surfaces.
- Task 156 moved the project into live benchmark proof mode.
- The first live proof attempts showed that runtime transport reliability and completion integrity now matter more than additional architectural surface area.

## What the product can honestly claim today

The repo has deterministic proof for a bounded supervised portfolio slice plus a narrow one-task autonomous safe lane, and it now has the first live benchmark execution path for one-task proof-mode work.

It can honestly claim:

- supervised local-first progression across registered project surfaces,
- project-scoped workspace/branch/state isolation,
- bounded one-task autonomous execution with role-separated artifacts,
- targeted self-heal and measured failure surfaces,
- benchmark/session artifacts for one-task proof-mode work,
- compatibility-preserving hosted-authority and merge-eligibility truth.

The proof is intentionally bounded and does **not** claim:

- arbitrary protected/controller task-list autonomy,
- broad unattended production scheduling across arbitrary task families,
- arbitrary multi-task autonomous execution,
- or broad self-hosting app-building autonomy.

## Next product-stage focus

The next product phase should optimize for **one-task execution reliability**, not more surface area.

That means:

- integrate strict no-manual-intervention scoreboarding into the live benchmark path,
- harden empty-bundle transport handling,
- normalize runtime artifact behavior,
- reject green-but-partial task completions,
- and re-prove one-task reliability on a fixed minipack before resuming broader roadmap ambitions.

Only after those criteria are met should the product consider bounded two-task trials again.
