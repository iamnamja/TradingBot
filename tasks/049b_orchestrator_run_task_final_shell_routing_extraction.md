# Task 049b — Run Task Final Shell Routing Extraction

## Goal

After wrapper/export dedupe, continue extracting the remaining reusable routing logic from `agents/run_task.py` into `agents/lib/*` so the shell becomes mostly argument parsing, top-level routing, and compatibility wrappers.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `tests/test_run_task_shell_parity.py`
- `tests/test_run_task_shell_convergence.py`
- `ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=main
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_shell_router_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Critical compatibility requirement

This task is about moving logic out of the shell, not redesigning behavior.

Do not change:

- branch discipline behavior
- runtime artifact cleanup behavior
- failure journal behavior
- spec/execution mode behavior
- validator wrapper behavior

## Required behavior

1. create a reusable routing helper module for the remaining nontrivial top-level shell routing
2. keep `agents.run_task.main()` as the public shell entrypoint
3. keep existing tests and command-line behavior green
4. add or update a convergence-oriented test proving the shell is thinner after extraction

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `agents/run_task.py` gets smaller and delegates more to `agents/lib/shell_router.py`
- public behavior remains compatible
