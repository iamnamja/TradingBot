# Orchestrator Roadmap (Tasks 015–020)

## Goal
Build the orchestration layer that automates the current human-in-the-loop task-delivery process.

## Roadmap summary
- 015: orchestrator state + backlog tracker
- 016: review/compliance checker
- 017: failure classifier
- 018: PR / CI / merge manager
- 019: repair workflow for task specs / runner
- 020: generic project adapter layer

## Task 015: Orchestrator state + backlog tracker
Purpose:
- track all tasks and their state
- know what task is next
- record current branch/PR/run status

Outputs:
- state model
- simple status file or state store
- backlog scanner

## Task 016: Review/compliance checker
Purpose:
- inspect branch diffs and results
- verify deliverables were created
- detect out-of-scope file changes
- detect committed runtime artifacts
- determine whether task output is mergeable

Outputs:
- mergeable / not-mergeable verdict
- reasons and suggested remediation

## Task 017: Failure classifier
Purpose:
- classify failed runs into categories:
  - implementation bug
  - task ambiguity
  - runner weakness
  - CI/dependency issue
  - repo hygiene issue
- decide whether to retry, patch task, patch runner, or stop

Outputs:
- structured failure classification
- recommended next action

## Task 018: PR / CI / merge manager
Purpose:
- create PRs
- wait/poll for CI status
- merge if policy allows
- sync local main after merge

Outputs:
- PR automation
- CI status handling
- safe merge logic

## Task 019: Repair workflow
Purpose:
- automate the workflow for patching:
  - task specs
  - runner
  - CI/workflows
- enforce approval gates for meta changes

Outputs:
- repair workflow
- approval-needed states
- safe task rerun after repair

## Task 020: Generic project adapter layer
Purpose:
- make the orchestrator reusable beyond TradingBot

Outputs:
- project config schema
- TradingBot adapter
- project-specific command mapping
- protected-files configuration
- generic engine / specific adapter separation

## After 020
Once 015–020 are complete, the orchestrator should be able to continue the TradingBot backlog with much less manual involvement.

Future TradingBot tasks can then focus again on product functionality rather than delivery mechanics.
