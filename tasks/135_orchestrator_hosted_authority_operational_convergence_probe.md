# Task 135 — Orchestrator hosted-authority operational convergence probe

## Goal
Keep hosted-authority truth aligned with the repo’s real operational state so unattended claims remain honest when checks are absent, weak, or not enforced.

## Scope
- repo check contract vs actual `gh pr checks` evidence
- required-check discovery and missing-check posture
- branch-protection / unattended-safety narrative

## Required changes
- make `no checks reported` an explicit operational-convergence signal, not just a textual note
- surface whether the repo is actually ready for unattended merge progression
- keep local truth and hosted truth clearly separated in reports and docs
- avoid broadening autonomy claims when operational convergence is weak

## Acceptance
- focused tests cover missing checks, misconfigured checks, and satisfied checks
- runtime/reporting surfaces make unattended readiness explicit
- docs remain narrowly truthful about hosted authority
