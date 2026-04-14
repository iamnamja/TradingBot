# Task 188 — orchestrator Codex patch transport and dual-mode output parsing

## Status

This task is now treated as an umbrella and should be executed through two focused subtasks because the original surface spans both protected and normal file lanes.

## Split plan

- `tasks/188a_orchestrator_codex_patch_transport_parser_and_apply_adapter.md`
- `tasks/188b_orchestrator_run_task_dual_transport_selection_and_protected_surface_integration.md`

## Why the split

The original task spans:
- normal transport/parser work (`agents/lib/bundle_parser.py`, `agents/lib/patch_apply.py`, tests)
- protected-surface runner integration (`agents/run_task.py`)
- docs/task updates

That combination repeatedly triggers protected-method-mode transport failures before code validation.

## Operator note

Do not run this umbrella task directly. Run 188a first, merge it, then run 188b.
