# Task 131 — Orchestrator empty/underfilled bundle failure classification

## Goal
Classify empty bundle, underfilled bundle, markerless transport, and generic malformed bundle as distinct failure types so retries can be targeted.

## Scope
- bundle parser / shell routing failure evidence
- failure-journal categories and remediation plans
- conservative retry vs escalate posture

## Required changes
- add explicit classification for zero-file bundle responses
- add explicit classification for structurally valid but underfilled bundles
- preserve existing malformed-transport handling for marker/order problems
- expose the distinct categories through stable failure-journal / runtime seams

## Acceptance
- focused tests distinguish empty bundle, underfilled bundle, and malformed transport
- remediation plans differ appropriately by failure type
- no docs claim broader unattended autonomy
