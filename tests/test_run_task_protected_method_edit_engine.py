import importlib.util
from pathlib import Path
import sys

import pytest


def _load_run_task_module():
    module_path = Path("agents") / "run_task.py"
    spec = importlib.util.spec_from_file_location("agents.run_task", module_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _method_bundle(path: str, name: str, body: str = "return 1") -> str:
    return "\n".join(
        [
            "BEGIN_METHOD_INSERTION",
            f"TARGET_FILE: {path}",
            f"METHOD_NAME: {name}",
            "BEGIN_METHOD",
            f"def {name}(self):",
            f"    {body}",
            "END_METHOD",
            "END_METHOD_INSERTION",
            "",
        ]
    )


def test_request_and_parse_method_insertion_uses_negotiated_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    run_task = _load_run_task_module()

    # Simulate capability negotiation that applies a safe fallback model for method-insertion
    monkeypatch.setattr(
        run_task,
        "negotiate_model_capability",
        lambda **kwargs: {
            "provider": "openai",
            "requested_model": "gpt-5-codex",
            "required_transport": "method_insertion",
            "compatible": True,
            "fallback_applied": True,
            "selected_provider": "openai",
            "selected_model": "gpt-5",
            "selected_output_transport": "file_bundle",
            "selected_transport_contract": "strict_file_bundle",
            "reason": "fallback selected",
            "status": "fallback",
        },
    )

    seen: dict[str, str] = {}

    def _fake_chat(messages, model, provider=None):
        seen["model"] = model
        seen["provider"] = provider
        # Return a valid method insertion bundle for the expected path/method
        return _method_bundle("agents/run_task.py", "helper", "return 3")

    monkeypatch.setattr(run_task, "chat", _fake_chat)

    out_path = tmp_path / "last_output.txt"
    method_text = run_task.request_and_parse_method_insertion(
        messages=[{"role": "user", "content": "please add helper"}],
        model="gpt-5-codex",  # requested model that will fall back
        provider="openai",
        last_output_path=out_path,
        expected_path="agents/run_task.py",
        expected_method_name="helper",
    )

    assert "def helper(self):" in method_text
    assert "return 3" in method_text
    # The actual provider/model used should be the negotiated (fallback) selection
    assert seen["provider"] == "openai"
    assert seen["model"] == "gpt-5"
    # Transport observability sidecar files are emitted
    assert (tmp_path / "_last_provider_call_path.txt").exists()
    assert (tmp_path / "_last_raw_output_meta.txt").exists()


def test_request_and_parse_method_insertion_stops_without_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    run_task = _load_run_task_module()

    # Simulate a model that does not support the required transport and no fallback is applied
    monkeypatch.setattr(
        run_task,
        "negotiate_model_capability",
        lambda **kwargs: {
            "provider": "openai",
            "requested_model": "gpt-5-codex",
            "required_transport": "method_insertion",
            "compatible": False,
            "fallback_applied": False,
            "selected_provider": "openai",
            "selected_model": "gpt-5-codex",
            "selected_output_transport": "patch",
            "selected_transport_contract": "patch_apply_mode",
            "reason": "mismatch",
            "status": "mismatch",
        },
    )

    with pytest.raises(run_task.FileBundleError) as excinfo:
        run_task.request_and_parse_method_insertion(
            messages=[{"role": "user", "content": "please add helper"}],
            model="gpt-5-codex",
            provider="openai",
            last_output_path=tmp_path / "last_output.txt",
            expected_path="agents/run_task.py",
            expected_method_name="helper",
        )

    assert "mismatch" in str(excinfo.value).lower()


def test_partition_preflight_emits_protected_method_trace(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    run_task = _load_run_task_module()

    # Ensure calls that may read/write relative artifacts do so under the temp directory
    cwd = Path.cwd()
    try:
        # Change working directory to tmp_path for isolated artifact emission
        import os

        os.chdir(tmp_path)

        # Force a deterministic capability negotiation snapshot for method_insertion
        monkeypatch.setattr(
            run_task,
            "negotiate_model_capability",
            lambda **kwargs: {
                "provider": "openai",
                "requested_model": "gpt-5",
                "required_transport": "method_insertion",
                "compatible": True,
                "fallback_applied": False,
                "selected_provider": "openai",
                "selected_model": "gpt-5",
                "selected_output_transport": "file_bundle",
                "selected_transport_contract": "strict_file_bundle",
                "reason": "compatible",
                "status": "compatible",
            },
        )

        # Partition with a protected meta harness path present
        normal, protected = run_task._partition_required_paths_for_normal_bundle(
            ["README.md", "agents/run_task.py"],
            protected_targets=[{"path": "agents/run_task.py", "mode": "replace", "method_name": "helper"}],
        )

        # Partition should separate protected meta harness
        assert "agents/run_task.py" in protected
        assert "README.md" in normal

        # Verify protected-method preflight artifact is written and minimally correct
        preflight = Path("_last_protected_method_preflight.json")
        assert preflight.exists(), "preflight trace should be emitted"
        payload = __import__("json").loads(preflight.read_text(encoding="utf-8"))
        assert payload["artifact_type"] == "protected_method_preflight"
        assert payload["transport_preflight"]["required_transport"] == "method_insertion"
        assert payload["transport_preflight"]["fallback_attempted"] is True  # allow_fallback=True is used in preflight
        assert payload["retry_policy"]["policy_kind"] in {"two_phase_parse_recovery"}
        # Selection rationale should be present and reference the protected mode
        assert payload["selection"] in {"protected", "normal_only"}
        assert isinstance(payload["partition_result"]["protected_paths"], list)
    finally:
        import os

        os.chdir(cwd)
