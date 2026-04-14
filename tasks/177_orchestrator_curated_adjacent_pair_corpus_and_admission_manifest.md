# Task 177 — orchestrator curated adjacent-pair corpus and admission manifest

## Why

A bounded supervised two-task pilot should be exercised on a curated, inspectable set of adjacent task pairs rather than ad hoc choices. The repo needs a durable pair corpus and manifest schema so pilot evidence is reproducible and explicit.

## Scope

Create a curated adjacent-pair corpus and manifest format for bounded pilot runs.

## Runtime seams to reuse

- Reuse the exact two-task bounded pilot runner from Task 176.
- Reuse the admission truth from Task 171 and handoff truth from Task 172.
- Reuse benchmark/canary artifact naming conventions from Tasks 174–175.

## Requirements

- Define a manifest schema for bounded two-task pilot pairs.
- Each pair entry should persist at minimum:
  - pair id,
  - task A path/id,
  - task B path/id,
  - expected adjacency/handoff relationship,
  - whether the pair is benchmark-eligible for the bounded pilot,
  - optional supervision profile or notes.
- Include both:
  - positive/eligible pairs,
  - and negative cases such as blocked, incompatible, or ineligible pairs.
- Keep the corpus curated and explicit.
- Do **not** auto-discover arbitrary task chains from the backlog in this task.

## Non-goals

- Do not generate a general planner for arbitrary pair selection.
- Do not widen beyond curated adjacent pairs.

## Acceptance criteria

- Tests prove the manifest parser/loader preserves pair truth explicitly.
- Tests prove positive and negative pairs are distinguishable and durable.
- Tests prove the bounded pilot runner can consume the curated pair manifest without widening scope.
