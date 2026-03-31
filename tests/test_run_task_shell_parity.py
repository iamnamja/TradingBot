from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from typing import Any

import pytest


def _import_run_task_module() -> Any:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return importlib.import_module("agents.run_task")


def _write_task_file(tmp_path: Path, body: str = "Implement feature safely") -> Path:
    task_file = tmp_path / "task.md"
    task_file.write_text(body, encoding="utf-8")
    return task_file


def test_provider_wrapper_delegates_to_extracted_module(monkeypatch: pytest.MonkeyPatch) -> None:
    run_task = _import_run_task_module()
    provider_client = importlib.import_module("agents.lib.provider_client")

    def _fake_chat(messages: list[dict[str, str]], model: str, provider: str | None = None) -> str:
        assert messages == [{"role": "user", "content": "x"}]
        assert model == "m"
        assert provider == "openai"
        return "OK"

    monkeypatch.setattr(provider_client, "chat", _fake_chat)

    assert run_task.chat([{"role": "user", "content": "x"}], model="m", provider="openai") == "OK"


def test_parser_policy_and_semantic_wrappers_delegate_to_extracted_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    run_task = _import_run_task_module()
    bundle_parser = importlib.import_module("agents.lib.bundle_parser")
    protected_file_policy = importlib.import_module("agents.lib.protected_file_policy")
    semantic_preflight = importlib.import_module("agents.lib.semantic_preflight")

    calls: dict[str, bool] = {
        "bundle": False,
        "policy": False,
        "semantic": False,
    }

    def _fake_parse_file_bundle(**kwargs: Any) -> dict[str, str]:
        calls["bundle"] = True
        return {"x.txt": "hi\n"}

    def _fake_parse_harness_file_policies(**kwargs: Any) -> dict[str, dict[str, object]]:
        calls["policy"] = True
        return {}

    def _fake_validate_static_bundle_contracts(bundle: dict[str, str], task_text: str) -> tuple[bool, str]:
        calls["semantic"] = True
        return True, ""

    monkeypatch.setattr(bundle_parser, "parse_file_bundle", _fake_parse_file_bundle)
    monkeypatch.setattr(protected_file_policy, "parse_harness_file_policies", _fake_parse_harness_file_policies)
    monkeypatch.setattr(semantic_preflight, "validate_static_bundle_contracts", _fake_validate_static_bundle_contracts)

    parsed = run_task.parse_file_bundle("BEGIN_FILE_BUNDLE\nFILE: x.txt\nhi\nEND_FILE\nEND_FILE_BUNDLE\n")
    assert parsed == {"x.txt": "hi\n"}
    assert run_task.parse_harness_file_policies("## Harness policy\n") == {}
    ok, msg = run_task.validate_static_bundle_contracts({}, "task")
    assert ok is True
    assert msg == ""
    assert calls == {"bundle": True, "policy": True, "semantic": True}


def test_main_keeps_cli_surface_and_delegates_post_parse_routing() -> None:
    src = ast.parse(Path("agents/run_task.py").read_text(encoding="utf-8"))
    main_node = next(n for n in src.body if isinstance(n, ast.FunctionDef) and n.name == "main")

    arg_names: list[str] = []
    delegate_call_present = False
    for node in ast.walk(main_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "ap" and node.func.attr == "add_argument":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    arg_names.append(node.args[0].value)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "route_shell_main":
            delegate_call_present = True

    expected_args = {
        "task",
        "--push",
        "--provider",
        "--model",
        "--max-iters",
        "--policy-block-limit",
        "--spec-mode",
        "--bootstrap-project",
        "--keep-runtime-artifacts",
    }
    assert set(arg_names) == expected_args
    assert delegate_call_present is True
