# Task 049 — Run Task Shell Convergence (Umbrella)

## Goal

Finish the thin-shell job on `agents/run_task.py`.

Tasks 042–048 extracted major logic into `agents/lib/*`, but the shell is still too large and still contains duplicate wrapper/export definitions.

This umbrella task should **not** be run directly.

## Split

Run these in order:

1. `049a_orchestrator_run_task_export_and_wrapper_dedupe`
2. `049b_orchestrator_run_task_final_shell_routing_extraction`

## Intent

The goal is not to add a new capability tranche.

The goal is to:

- remove duplicate public wrapper/export definitions in `agents/run_task.py`
- preserve existing behavior and compatibility seams
- continue moving reusable logic into `agents/lib/*`
- leave `run_task.py` as a stable thin public entrypoint

## Run guidance

- `049a` is a **file-level convergence** task on `agents/run_task.py`; treat it as a surgical shell patch, not as protected method-replacement work
- `049b` resumes **targeted extraction** after the duplicate wrapper/export surfaces are converged
- do not run this umbrella file directly through the harness

## Exit condition for 049

Task 049 is complete when:

- `agents/run_task.py` has one active definition per targeted public wrapper/export seam
- the shell is smaller and routes more through reusable helpers under `agents/lib/*`
- shell parity, runtime foundations, and spec/execution compatibility remain green
