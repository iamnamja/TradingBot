# Task 049b — Run Task Final Shell Routing Extraction

## Goal

After 049a wrapper/export convergence, continue extracting the remaining reusable routing logic from `agents/run_task.py` into `agents/lib/*` so the shell becomes thinner while preserving the public CLI surface and the stabilized compatibility seams.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `tests/test_run_task_shell_parity.py`
- `tests/test_run_task_shell_convergence.py`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=main
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_shell_router_exports ANCHOR_BEFORE=if __name__ == "__main__":
- FILE: agents/lib/shell_router.py MODE=ALLOW_CREATE
- FILE: tests/test_run_task_shell_parity.py MODE=TESTS_ONLY
- FILE: tests/test_run_task_shell_convergence.py MODE=TESTS_ONLY

## Critical compatibility requirement

This task is about moving reusable routing logic out of the shell, not redesigning the shell.

Do not change:

- branch discipline behavior
- runtime artifact cleanup behavior
- failure journal behavior
- spec/execution mode behavior
- validator wrapper behavior
- repo bootstrap/import behavior required for the shell to import `agents.lib.*`

## Task-shape guidance

Keep the `agents/run_task.py` changes tightly focused on:

- `main()`
- the additive `_shell_router_exports()` helper

`main()` must remain the visible public CLI shell.

That means `main()` must continue to own:

- `argparse.ArgumentParser(...)` construction
- the `ap.add_argument(...)` CLI declarations
- argument parsing from `argv`
- the top-level `if args.*` shell entry decisions that define the public command-line surface

Only extract the reusable routing and execution flow that happens after the CLI surface is defined and parsed.

If `main()` needs access to new routing helpers, prefer a local import inside `main()` or inside `_shell_router_exports()` so the task does not expand into broad top-of-file shell churn.

Do not reintroduce duplicate wrapper/export definitions that 049a removed.

Do not move or rename existing stabilized wrapper/export seams unless a parity test is updated to prove compatibility is preserved.

## Required behavior

1. create a reusable routing helper module for the remaining nontrivial post-parse shell routing
2. keep `agents.run_task.main()` as the public shell entrypoint
3. keep the visible CLI argument declaration surface in `main()`
4. keep existing tests and command-line behavior green
5. add or update a convergence-oriented test proving the shell is thinner after extraction
6. preserve compatibility with the wrapper/export seams stabilized in 043–049a
7. preserve the single-definition convergence invariant for targeted exports, including `_spec_mode_exports()`

## Extraction boundary

The new routing helper should own reusable post-parse flow such as:

- selecting the execution path after arguments are parsed
- delegating to reusable shell-routing branches
- coordinating reusable execution steps that do not need to remain inline in `main()`

The new routing helper must not require an incompatible call shape from `main()`.

Preferred compatibility shapes:

- either `route_shell_main()` is callable with no required arguments and internally captures what it needs via exported shell helpers
- or `main()` explicitly passes a local `shell_env` / helper mapping when calling it

Whichever shape is chosen, it must be covered by parity tests and must not break direct invocation from `main()`.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `agents/run_task.py` gets smaller and delegates more to `agents/lib/shell_router.py`
- `tests/test_run_task_shell_convergence.py` proves no targeted duplicate wrapper/export surface was reintroduced
- `tests/test_run_task_shell_parity.py` proves the visible CLI declaration surface remains in `main()` while post-parse routing delegates outward
- public behavior remains compatible
