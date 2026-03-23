from __future__ import annotations

import ast
from pathlib import Path


TARGET_EXPORTS = {
    "_runtime_foundations_exports",
    "_parser_policy_exports",
    "_semantic_preflight_exports",
    "_artifact_quarantine_exports",
    "_spec_mode_exports",
    "_failure_journal_exports",
    "_validator_runner_exports",
    "_bootstrap_exports",
    "_shell_router_exports",
}


def _function_defs(module_path: str) -> list[ast.FunctionDef]:
    tree = ast.parse(Path(module_path).read_text(encoding="utf-8"))
    return [n for n in tree.body if isinstance(n, ast.FunctionDef)]


def test_targeted_export_helpers_remain_single_definition() -> None:
    names = [fn.name for fn in _function_defs("agents/run_task.py")]
    for target in TARGET_EXPORTS:
        assert names.count(target) == 1, f"duplicate export helper detected: {target}"


def test_shell_router_module_exposes_route_entrypoint() -> None:
    names = [fn.name for fn in _function_defs("agents/lib/shell_router.py")]
    assert names.count("route_shell_main") == 1


def test_main_routes_to_shell_router_after_parse() -> None:
    tree = ast.parse(Path("agents/run_task.py").read_text(encoding="utf-8"))
    main_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")

    has_exports_lookup = False
    has_route_call = False
    for node in ast.walk(main_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "exports":
                    if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                        if node.value.func.id == "_shell_router_exports":
                            has_exports_lookup = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "route_shell_main":
            has_route_call = True

    assert has_exports_lookup is True
    assert has_route_call is True
