from pathlib import Path


def _import_run_task_module():
    import sys
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import agents.run_task as run_task
    return run_task


def test_method_insertion_writes_transport_observability_artifacts(monkeypatch, tmp_path):
    run_task = _import_run_task_module()
    bundle = "\n".join([
        "BEGIN_METHOD_INSERTION",
        "TARGET_FILE: agents/run_task.py",
        "METHOD_NAME: helper",
        "BEGIN_METHOD",
        "def helper(self):",
        "    return 3",
        "END_METHOD",
        "END_METHOD_INSERTION",
        "",
    ])

    monkeypatch.setattr(run_task, "chat", lambda messages, model, provider: bundle)

    out_path = tmp_path / "last_output.txt"
    result = run_task.request_and_parse_method_insertion(
        messages=[{"role": "user", "content": "please help"}],
        model="gpt-5",
        provider="openai",
        last_output_path=out_path,
        expected_path="agents/run_task.py",
        expected_method_name="helper",
    )
    assert "def helper" in result
    call_artifact = tmp_path / "_last_provider_call_path.txt"
    meta_artifact = tmp_path / "_last_raw_output_meta.txt"
    assert call_artifact.exists()
    assert meta_artifact.exists()
    call_text = call_artifact.read_text(encoding="utf-8")
    meta_text = meta_artifact.read_text(encoding="utf-8")
    assert "phase: method_insertion.initial" in call_text
    assert "provider: openai" in call_text
    assert "raw_output_nonempty: True" in meta_text


def test_bundle_writes_transport_observability_artifacts(monkeypatch, tmp_path):
    run_task = _import_run_task_module()
    bundle = "\n".join([
        "BEGIN_FILE_BUNDLE",
        "FILE: sample.txt",
        "hello",
        "END_FILE",
        "END_FILE_BUNDLE",
        "",
    ])

    monkeypatch.setattr(run_task, "chat", lambda messages, model, provider: bundle)

    out_path = tmp_path / "last_output.txt"
    parsed = run_task.request_and_parse_bundle(
        messages=[{"role": "user", "content": "please help"}],
        model="gpt-5",
        provider="openai",
        last_output_path=out_path,
        expected_paths=["sample.txt"],
    )
    assert parsed["sample.txt"] == "hello\n"
    call_artifact = tmp_path / "_last_provider_call_path.txt"
    meta_artifact = tmp_path / "_last_raw_output_meta.txt"
    assert call_artifact.exists()
    assert meta_artifact.exists()
    call_text = call_artifact.read_text(encoding="utf-8")
    meta_text = meta_artifact.read_text(encoding="utf-8")
    assert "phase: bundle.initial" in call_text
    assert "required_transport: file_bundle" in meta_text
