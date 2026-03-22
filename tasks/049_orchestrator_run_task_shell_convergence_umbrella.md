# Task 049 — Run Task Shell Convergence (Umbrella)

## Goal

Finish the thin-shell job on `agents/run_task.py`.

Tasks 042–048 extracted major logic into `agents/lib/*`, but the shell is still too large and still contains duplicate wrapper/export definitions.

This umbrella task should **not** be run directly.

## Split

Run these in order:

- `049a_orchestrator_run_task_export_and_wrapper_dedupe`
- `049b_orchestrator_run_task_final_shell_routing_extraction`

## Intent

The goal is not to add a large new capability.

The goal is to:

- remove duplicate public wrapper/export definitions in `agents/run_task.py`
- preserve existing behavior and compatibility seams
- continue moving reusable logic into `agents/lib/*`
- leave `run_task.py` as a stable thin public entrypoint
