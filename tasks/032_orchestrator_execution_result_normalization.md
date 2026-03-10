\# Task 032 — Orchestrator Execution Result Normalization



\## Goal

Normalize raw task-runner output into a stable execution result contract.



\## Why

Task 031 introduces real execution. The orchestrator must now interpret output reliably across success and failure cases.



\## Scope



Build a normalization layer that converts raw execution output into a stable result object.



\## Deliverables



Create or update:



\- `src/builder/orchestrator/execution\_result.py`

\- `src/builder/orchestrator/runner.py`

\- `tests/test\_orchestrator\_execution\_result.py`



\## Required behavior



The normalizer must return a structured object:

{

"success": bool,

"status": str,

"output": str,

"failure\_text": str,

"changed\_files": list,

"deliverables\_updated": list,

"raw\_stdout": str,

"raw\_stderr": str,

"returncode": int

}





The normalizer must support:



\- successful task execution

\- lint/test failure

\- missing deliverables

\- malformed output

\- unknown failure fallback



Runner must use the normalized result instead of parsing stdout directly.



\## Acceptance criteria



Tests cover:



\- success case

\- failed checks

\- missing deliverables

\- malformed output

\- unknown failure fallback

