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
- FILE: tests/test_run_task_shell_parity.py MODE=TESTS_ONLY
- FILE: tests/test_run_task_shell_convergence.py MODE=TESTS_ONLY
- FILE: ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY

## Critical compatibility requirement

This task is about moving logic out of the shell, not redesigning behavior.

Do not change:

- branch discipline behavior
- runtime artifact cleanup behavior
- failure journal behavior
- spec/execution mode behavior
- validator wrapper behavior

## Task-shape guidance

Keep the `agents/run_task.py` changes tightly focused on:

- `main()`
- the additive `_shell_router_exports()` helper

If `main()` needs access to new routing helpers, prefer a local import inside `main()` or inside `_shell_router_exports()` so the task does not expand into broad top-of-file shell churn.

Do not reintroduce duplicate wrapper/export definitions that `049a` just removed.

## Required behavior

1. create a reusable routing helper module for the remaining nontrivial top-level shell routing
2. keep `agents.run_task.main()` as the public shell entrypoint
3. keep existing tests and command-line behavior green
4. add or update a convergence-oriented test proving the shell is thinner after extraction
5. preserve compatibility with the wrapper/export seams stabilized in 043–049a

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `agents/run_task.py` gets smaller and delegates more to `agents/lib/shell_router.py`
- `tests/test_run_task_shell_convergence.py` proves no targeted duplicate wrapper/export surface was reintroduced
- public behavior remains compatible
