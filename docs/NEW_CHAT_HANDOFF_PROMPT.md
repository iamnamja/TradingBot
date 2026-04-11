# New Chat Handoff Prompt

We are in the orchestrator reliability program.

Completed
- Tasks 157 through 161 merged.
- The first reliability minipack re-proof completed and the outcome was to remain in one-task reliability mode.

Current goal
- Execute the second reliability sprint sequentially:
  - 162 authority-gate evidence narrowing
  - 163 deliverable contract and completion prompt hardening
  - 164 runtime artifact hygiene and typo normalization
  - 165 one-task reliability minipack re-proof v2

Working conventions
- Use clean main before each orchestrator-run task.
- Prefer `py -m agents.run_task ... --push --keep-runtime-artifacts --provider openai --model gpt-5`.
- Treat mid-run manual file edits as failed autonomous attempts for benchmark purposes.
- Use small manual fixes only when the runtime itself is the blocker.
