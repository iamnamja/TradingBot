# New chat handoff prompt

Use the following prompt when starting the next chat in this project.

---

I’m continuing work on the TradingBot orchestrator project. Please use the attached current `agents`, `docs`, `tasks`, and `tests` snapshots as the source of truth.

Where we are:
- Reliability/autonomy continuation 055–067 is complete, including 065a and 067a.
- Stabilization extension tasks 068a–068c were added because protected/controller tasks were still not autonomous enough and `agents/run_task.py` was too central.
- 068a and 068b were manually landed to harden protected-lane execution and duplicate bundle recovery.
- 068c was landed to continue the first controller decomposition.
- Original Task 068 (`orchestrator_task_scope_and_split_heuristics`) still needs to be retried/confirmed after the stabilization work.
- The next continuation after 068 is a new backlog-execution tranche (069–075) focused on:
  - continuing to thin `agents/run_task.py`
  - adding a task-list manifest and queue model
  - batch state persistence and resume
  - per-task checkpoint/isolation
  - explicit post-task continue/stop/manual policy
  - a user-facing batch runner CLI
  - an end-to-end backlog execution proof

Important working style:
- We have repeatedly needed manual patches for protected/controller tasks.
- We now verify branch diffs against exact task deliverables rather than trusting stale `_last_agent_patch*` files.
- Deliverable completeness matters: if a task lists exact files, they must all be updated before the task is considered complete.
- When a protected/controller task fails, prefer diagnosing whether the autonomous lane is missing capability before just forcing another manual patch.
- The long-term goal is to make the orchestrator capable of taking a list of tasks and working through them conservatively and automatically.

How to help next:
1. Review the current code/docs/tasks state from the attached files.
2. Treat `tasks/README.md` and the numbered task files as the canonical ordering.
3. Assume the immediate near-term sequence is:
   - retry/confirm original 068
   - then proceed into 069–075
4. If I ask you to patch or continue the work, give me:
   - a full zip of changed files when multiple files are involved
   - exact PowerShell steps to overwrite, validate, commit, merge, and continue
   - guidance on whether a task is suitable for autonomous rerun or should be handled as a manual patch

---

## Files to provide to the new chat

At minimum, attach:
- `agents.zip`
- `docs.zip`
- `tasks.zip`
- `tests.zip`

If there is an active failed run you want diagnosed too, also attach:
- `_last_agent_model_output.txt`
- `_last_agent_file_bundle.txt`
