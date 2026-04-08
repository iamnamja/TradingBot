# Task 133 — Orchestrator assertion-to-compatibility surface planner

## Goal
Repair coupled compatibility/public-surface drift as one small planned set rather than fixing only the first visible failing assertion.

## Scope
- failing exported-key, snapshot, enum/value, and public-surface assertions
- run_task export seams plus underlying library/provider seams
- minimal coupled repair-set inference

## Required changes
- extend assertion-driven repair targeting to infer coupled compatibility seams
- prefer small explicit repair sets such as export seam + source module, rather than one-file symptom chasing
- surface the chosen coupled repair set in failure-journal / controller repair context
- preserve bounded minimal-patch posture

## Acceptance
- focused tests cover missing exported key, missing snapshot field, and alias/value drift cases
- repair planning selects the minimal coupled target set instead of a broad builder rewrite
- no broader scope claim is introduced
