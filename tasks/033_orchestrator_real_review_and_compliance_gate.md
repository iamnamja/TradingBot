\# Task 033 — Real Review and Compliance Gate



\## Goal

Evaluate actual execution results and changed files before allowing merge readiness.



\## Why

Once execution becomes real, review must use real execution outputs.



\## Deliverables



Update:



\- `src/builder/orchestrator/runner.py`

\- `src/builder/orchestrator/review.py`

\- `src/builder/orchestrator/policy.py`

\- `tests/test\_orchestrator\_real\_review\_gate.py`



\## Required behavior



Review must determine:



\- mergeable

\- review\_blocked

\- approval\_required



Policy engine must check changed files against approval rules.



Execution result must only become `ready\_for\_pr` if:



\- execution succeeded

\- review passed

\- policy allows merge



\## Acceptance criteria



Tests cover:



\- mergeable success

\- missing deliverables

\- approval-required file changes

\- no changed files edge case

