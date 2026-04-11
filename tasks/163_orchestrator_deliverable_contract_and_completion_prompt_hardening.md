# Task 163: orchestrator deliverable contract and completion prompt hardening

Goal

Improve one-task completion quality by making deliverable contracts and completion prompts more explicit, especially for tasks that require wiring into existing live surfaces rather than adding only helper modules.

Why this matters

The first re-proof showed that the orchestrator can still produce partial work that passes local helper tests but does not fully integrate into the live path the task intended to change.

Create or update these exact files
- agents/run_task.py
- agents/lib/completion_integrity.py
- tests/test_completion_integrity.py
- tasks/163_orchestrator_deliverable_contract_and_completion_prompt_hardening.md
- docs/TRADINGBOT_PROJECT_STATE.md

Scope
- Tighten task-text parsing for:
  - exact deliverable contracts
  - required existing-surface touch requirements
  - re-proof / proof task wording
- Improve the prompt feedback appended after a completion-integrity failure so the next iteration is more likely to touch the correct live surface.
- Keep the gate bounded and mechanical. This task is not about scoring quality heuristically; it is about making the contract and repair prompt more explicit.

Acceptance criteria
- Completion-integrity directive parsing supports explicit existing-surface requirements robustly.
- The runner appends clearer feedback when a bundle is rejected for helper-only or new-surface-only completion.
- Tests cover at least one helper-only failure and one existing-surface success case driven by the prompt/contract shape.
- Project state docs note that completion integrity now depends both on the task contract and the follow-up repair prompt.

Update discipline
When updating an existing file, preserve the current architecture and surrounding code unless the task explicitly requires a rewrite.
Do not replace large existing files with miniature standalone versions or toy implementations.
