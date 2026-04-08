# Task 132 — Orchestrator missing-deliverable retry compiler

## Goal
When the model returns a structurally valid but incomplete patch, retry using exact missing-deliverable evidence instead of a generic transport reminder.

## Scope
- required deliverables vs parsed bundle comparison
- unchanged-required-file detection where relevant
- retry prompt compilation and artifact logging

## Required changes
- compile retry feedback around the exact required files still missing or unchanged
- keep bundle-format reminders only for true transport problems
- record the missing-deliverable evidence in failure artifacts and controller repair context
- avoid broad restatement of the entire task when only a small deliverable subset is missing

## Acceptance
- focused tests prove retries name the missing or unchanged required files
- incomplete but well-formed bundle responses no longer fall into generic malformed transport messaging
- full validation remains green
