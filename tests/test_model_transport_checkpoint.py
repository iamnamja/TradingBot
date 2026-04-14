from __future__ import annotations

import json
from pathlib import Path

from builder.orchestrator.model_transport_checkpoint import (
    collect_model_transport_evidence,
    evaluate_model_transport_checkpoint,
    write_model_transport_checkpoint,
)


def test_collect_model_transport_evidence_current_snapshot() -> None:
    evidence = collect_model_transport_evidence()

    assert evidence["docs_status"]["guard_ok"] is True
    assert evidence["model_profiles"]["gpt_profile_present"] is True
    assert evidence["model_profiles"]["codex_profile_present"] is True
    assert evidence["transport_support"]["gpt_file_bundle_preserved"] is True
    assert evidence["transport_support"]["codex_patch_declared"] is True
    assert evidence["transport_support"]["codex_method_requires_fallback"] is True


def test_evaluate_model_transport_checkpoint_is_conservative() -> None:
    evidence = collect_model_transport_evidence()
    evaluation = evaluate_model_transport_checkpoint(evidence)

    assert evaluation["verdict"] == "conditionally_ready_under_supervision"
    assert evaluation["policy"]["broad_unattended_multi_task_autonomy"] == "blocked"
    assert evaluation["policy"]["standalone_productization"] == "blocked"
    assert evaluation["evaluated_categories"]["docs_status_consistency_enforcement"] is True
    assert evaluation["evaluated_categories"]["proven_gpt_file_bundle_path_preserved"] is True


def test_write_model_transport_checkpoint(tmp_path: Path) -> None:
    evidence = collect_model_transport_evidence()
    evaluation = evaluate_model_transport_checkpoint(evidence)
    path = write_model_transport_checkpoint(str(tmp_path), evaluation, evidence_snapshot=evidence)

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["checkpoint_kind"] == "contract_and_model_transport_checkpoint"
    assert payload["evaluation"]["verdict"] == "conditionally_ready_under_supervision"
    assert "evidence" in payload
