from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from builder.orchestrator.transport_health import (
    aggregate_transport_health,
    compute_and_write_transport_health,
    evaluate_transport_stability_gate,
    write_transport_stability_checkpoint,
)


def test_aggregate_transport_health_synthetic_corpus() -> None:
    corpus: list[Dict[str, Any]] = [
        {
            "raw_capture_status": "non_empty",
            "parser_path": "bundle",
            "success": True,
            "fallback_applied": False,
        },
        {
            "raw_capture_status": "empty_zero_length",
            "parser_path": "bundle",
            "success": False,
            "failure_family": "bundle_parse_error",
            "fallback_applied": False,
        },
        {
            "raw_capture_status": "non_empty",
            "parser_path": "protected_method",
            "success": False,
            "failure_family": "method_insertion_failure",
            "fallback_applied": True,
        },
        {
            "raw_capture_status": "empty_whitespace_only",
            "parser_path": "bundle",
            "success": False,
            "failure_family": "bundle_parse_error",
            "fallback_applied": True,
        },
        {
            "raw_capture_status": "non_empty",
            "parser_path": "protected_method",
            "success": True,
            "fallback_applied": False,
        },
    ]

    summary, families = aggregate_transport_health(corpus)

    assert summary["run_count"] == 5
    assert summary["empty_capture_count"] == 2
    assert summary["bundle_parse_failure_count"] == 2
    assert summary["method_insertion_failure_count"] == 1
    assert summary["fallback_count"] == 2

    assert families == {
        "bundle_parse_error": 2,
        "method_insertion_failure": 1,
    }


def test_write_transport_health_artifacts(tmp_path: Path) -> None:
    corpus: list[Dict[str, Any]] = [
        {
            "raw_capture_status": "non_empty",
            "parser_path": "bundle",
            "success": True,
            "fallback_applied": False,
        },
        {
            "raw_capture_status": "failed_before_payload",
            "parser_path": "method_insertion",
            "success": False,
            "failure_family": "method_insertion_failure",
            "fallback_applied": True,
        },
    ]

    summary, families, s_path, f_path = compute_and_write_transport_health(
        corpus, tmp_path
    )

    # Files exist
    assert s_path.exists()
    assert f_path.exists()

    # Names are correct
    assert s_path.name == "_transport_health_summary.json"
    assert f_path.name == "_transport_failure_families.json"

    # Contents match computed data
    loaded_summary = json.loads(s_path.read_text())
    loaded_families = json.loads(f_path.read_text())

    assert loaded_summary == summary
    assert loaded_families == families

    # Spot-check values for this corpus
    assert loaded_summary["run_count"] == 2
    assert loaded_summary["empty_capture_count"] == 1
    assert loaded_summary["bundle_parse_failure_count"] == 0
    assert loaded_summary["method_insertion_failure_count"] == 1
    assert loaded_summary["fallback_count"] == 1

    assert loaded_families == {"method_insertion_failure": 1}


def test_transport_stability_evaluation_is_conservative() -> None:
    # Build a small synthetic corpus that is healthy but below the "ready" sample-size gate.
    corpus: list[Dict[str, Any]] = [
        {"raw_capture_status": "non_empty", "parser_path": "bundle", "success": True, "fallback_applied": False},
        {"raw_capture_status": "non_empty", "parser_path": "bundle", "success": True, "fallback_applied": False},
        {"raw_capture_status": "non_empty", "parser_path": "protected_method", "success": True, "fallback_applied": True},
        {"raw_capture_status": "non_empty", "parser_path": "bundle", "success": False, "failure_family": "bundle_parse_error", "fallback_applied": False},
        {"raw_capture_status": "non_empty", "parser_path": "protected_method", "success": True, "fallback_applied": False},
        {"raw_capture_status": "non_empty", "parser_path": "protected_method", "success": True, "fallback_applied": False},
    ]
    summary, families = aggregate_transport_health(corpus)
    evaluation = evaluate_transport_stability_gate(summary, families, gpt_file_bundle_preserved=True)

    assert evaluation["counts"]["run_count"] == 6
    assert evaluation["evaluated_categories"]["proven_gpt_file_bundle_path_preserved"] is True
    # With conservative policy and small sample size, verdict should remain conditional at best.
    assert evaluation["verdict"] in {"conditionally_ready_under_supervision", "not_ready"}


def test_transport_stability_checkpoint_persists_payload(tmp_path: Path) -> None:
    # Minimal evaluation payload
    evaluation = {
        "verdict": "conditionally_ready_under_supervision",
        "counts": {"run_count": 3},
        "evaluated_categories": {"proven_gpt_file_bundle_path_preserved": True},
    }
    path = write_transport_stability_checkpoint(tmp_path, evaluation, evidence_snapshot={"summary": {"run_count": 3}, "families": {}})
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["checkpoint_kind"] == "transport_stability_checkpoint"
    assert data["evaluation"]["verdict"] == "conditionally_ready_under_supervision"
    assert data["evaluation"]["counts"]["run_count"] == 3
    assert "evidence" in data
