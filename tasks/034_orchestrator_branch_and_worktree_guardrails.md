\# Task 034 — Branch and Worktree Guardrails



\## Goal

Prevent orchestrator execution in unsafe git states.



\## Why

Real execution should never run on main or with a dirty worktree.



\## Deliverables



Create:



\- `src/builder/orchestrator/git\_guardrails.py`



Update:



\- `runner.py`

\- `cli.py`



Tests:



\- `tests/test\_orchestrator\_git\_guardrails.py`



\## Required behavior



Execution must fail when:



\- branch == main

\- worktree has uncommitted changes

\- branch name does not match task branch pattern



Simulation mode must bypass guardrails.



\## Acceptance criteria



Tests cover:



\- running on main

\- dirty worktree

\- valid branch

\- simulation bypass



