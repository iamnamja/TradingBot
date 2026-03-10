\# Task 036 — Resume After Approval



\## Goal

Allow orchestrator to resume execution after approval checkpoints.



\## Deliverables



Update:



\- `approval.py`

\- `runner.py`

\- `cli.py`



Tests:



\- `tests/test\_orchestrator\_resume\_after\_approval.py`



\## Required behavior



Runner must resume from latest approval checkpoint.



Resume must fail if approval not granted.



CLI must support:



--resume

