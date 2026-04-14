from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from agents.lib import provider_client as pc


def test_negotiate_model_capability_compatible_gpt_method_insertion() -> None:
    payload = pc.negotiate_model_capability(provider="openai", model="gpt-5", required_transport="method_insertion", allow_fallback=True)
    assert payload["compatible"] is True
    assert payload["fallback_applied"] is False
    assert payload["selected_model"] == "gpt-5"


def test_negotiate_model_capability_falls_back_from_codex_for_method_insertion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRADINGBOT_SAFE_FALLBACK_MODEL", raising=False)
    payload = pc.negotiate_model_capability(provider="openai", model="gpt-5-codex", required_transport="method_insertion", allow_fallback=True)
    assert payload["compatible"] is True
    assert payload["fallback_applied"] is True
    assert payload["selected_model"] == "gpt-5"


def test_negotiate_model_capability_can_explicitly_stop_without_fallback() -> None:
    payload = pc.negotiate_model_capability(provider="openai", model="gpt-5-codex", required_transport="method_insertion", allow_fallback=False)
    assert payload["compatible"] is False
    assert payload["status"] == "mismatch"
    assert payload["fallback_applied"] is False


def _import_run_task_module():
    root = Path(__file__).resolve().parents[1]
    import sys
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return importlib.import_module("agents.run_task")


def test_request_and_parse_method_insertion_uses_negotiated_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    run_task = _import_run_task_module()

    monkeypatch.setattr(run_task, "negotiate_model_capability", lambda **kwargs: {
        "provider": "openai",
        "requested_model": "gpt-5-codex",
        "required_transport": "method_insertion",
        "compatible": True,
        "fallback_applied": True,
        "selected_provider": "openai",
        "selected_model": "gpt-5",
        "selected_output_transport": "file_bundle",
        "reason": "fallback selected",
        "status": "fallback",
    })

    seen = {}
    def _fake_chat(messages, model, provider=None):
        seen["model"] = model
        seen["provider"] = provider
        return "BEGIN_METHOD_INSERTION\nTARGET_FILE: agents/run_task.py\nMETHOD_NAME: demo\nBEGIN_METHOD\ndef demo():\n    return 1\nEND_METHOD\nEND_METHOD_INSERTION"

    monkeypatch.setattr(run_task, "chat", _fake_chat)
    monkeypatch.setattr(run_task, "parse_method_insertion_bundle", lambda text, expected_path, expected_method_name: "def demo():\n    return 1\n")

    text = run_task.request_and_parse_method_insertion([{"role": "user", "content": "x"}], model="gpt-5-codex", provider="openai", last_output_path=tmp_path / "out.txt", expected_path="agents/run_task.py", expected_method_name="demo")
    assert "def demo" in text
    assert seen["model"] == "gpt-5"
    assert seen["provider"] == "openai"
    artifact = tmp_path / "_last_model_capability.txt"
    assert artifact.exists()


def test_request_and_parse_method_insertion_stops_on_incompatible_profile(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    run_task = _import_run_task_module()
    monkeypatch.setattr(run_task, "negotiate_model_capability", lambda **kwargs: {
        "provider": "openai",
        "requested_model": "gpt-5-codex",
        "required_transport": "method_insertion",
        "compatible": False,
        "fallback_applied": False,
        "selected_provider": "openai",
        "selected_model": "gpt-5-codex",
        "selected_output_transport": "patch",
        "reason": "requested model profile does not support required transport",
        "status": "mismatch",
    })

    with pytest.raises(run_task.FileBundleError):
        run_task.request_and_parse_method_insertion([{"role": "user", "content": "x"}], model="gpt-5-codex", provider="openai", last_output_path=tmp_path / "out.txt", expected_path="agents/run_task.py", expected_method_name="demo")
    artifact = tmp_path / "_last_model_capability.txt"
    assert artifact.exists()
    assert "mismatch" in artifact.read_text(encoding="utf-8")
