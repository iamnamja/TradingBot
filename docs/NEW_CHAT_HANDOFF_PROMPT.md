# New Chat Handoff Prompt

We are continuing work on the TradingBot orchestrator project.

Use the attached current `agents`, `docs`, `tasks`, `tests`, `README.md`, and `requirements.txt` snapshots as the source of truth.

Current state:
- Reliability/autonomy continuation and protected/controller stabilization are complete through 068–069.
- Backlog-execution continuation is complete through 075, including:
  - exact-deliverable parser/completion gate hardening
  - runtime-artifact retention switch
  - batch state persistence/resume
  - per-task checkpointing and continue gate
  - merge-ready validation hardening (074a–074c)
  - first conservative batch runner CLI and summary artifacts
  - first narrow end-to-end backlog execution proof
- The orchestrator is better, but it still is not yet a broad unattended scheduler.
- The next tranche is 076–082 and focuses on:
  - explicit final acceptance review/report
  - targeted self-heal for final-acceptance failures
  - a first-class batch executor/controller loop
  - accepted-task PR/check/merge/reset flow
  - resume-after-merge and resume-after-manual-resolution semantics
  - further decomposition of `agents/run_task.py`
  - a narrow autonomous backlog-runner proof for short ordinary-task manifests

Working style:
- Compare actual committed branch diff against exact task deliverables; do not trust stale `_last_agent_*` artifacts alone.
- Deliverable completeness matters: if the task lists exact files, all of them must be updated before the task is considered complete.
- Use `ruff check .` and `pytest -q` as the authoritative local validation profile before declaring success.
- If a run is green but exact required files are missing from committed `HEAD`, or unexpected tracked artifacts remain, treat the task as incomplete.
- Prefer targeted cleanup patches over blind reruns once a branch is close.
- Continue making `agents/run_task.py` less monolithic as new controller surfaces are introduced.

When helping next:
- follow `tasks/README.md` as the canonical ordering
- assume the immediate next planned sequence is 076–082
- when creating or updating tasks/docs, provide a zip of all changed files plus exact PowerShell merge steps
