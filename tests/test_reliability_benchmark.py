import json
import os
from typing import Dict, List

from builder.orchestrator.reliability_benchmark import (
    build_reliability_matrix,
    run_reliability_benchmark,
    evaluate_reliability_resume_gate,
    write_reliability_checkpoint,
)


def _write_json(path: str, payload: Dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def test_reliability_benchmark_writes_additive_artifacts_and_preserves_existing(tmp_path):
    base_dir = str(tmp_path)

    # Create existing one-task and two-task artifacts that must remain unchanged.
    one_task_scorecard = os.path.join(base_dir, "scorecard.json")
    two_task_summary = os.path.join(base_dir, "two_task", "bounded_corpus", "summary.json")

    one_task_original = {"existing": "one_task", "runs": [{"status": "green", "retries": 0}]}
    two_task_original = {"existing": "two_task", "sessions": [{"status": "green", "retries": 1}]}

    _write_json(one_task_scorecard, one_task_original)
    _write_json(two_task_summary, two_task_original)

    with open(one_task_scorecard, "r", encoding="utf-8") as f:
        before_one = f.read()
    with open(two_task_summary, "r", encoding="utf-8") as f:
        before_two = f.read()

    # Provide synthetic runs to ensure we do not need to parse unknown real shapes.
    one_task_runs: List[Dict] = [
        {
            "status": "green",
            "retries": 1,
            "failure_families": ["ADMISSION"],
            "supervised": False,
            "admission_blocked": False,
            "compatibility_regression": False,
        },
        {
            "status": "green",
            "retries": 2,
            "failure_families": ["COMPATIBILITY"],
            "supervised": True,
            "admission_blocked": False,
            "compatibility_regression": True,
        },
        {
            "status": "red",
            "retries": 3,
            "failure_families": ["ADMISSION"],
            "supervised": True,
            "admission_blocked": True,
            "compatibility_regression": False,
        },
    ]
    # Use the same synthetic set for two-task lane for simplicity in this test.
    two_task_sessions = list(one_task_runs)

    # Run the reliability benchmark, which must write only under reliability/.
    written = run_reliability_benchmark(
        base_dir=base_dir,
        one_task_runs=one_task_runs,
        two_task_sessions=two_task_sessions,
    )

    # Verify reliability artifacts exist and are written under a dedicated path.
    assert "matrix" in written and os.path.exists(written["matrix"])
    assert "one_task" in written and os.path.exists(written["one_task"])
    assert "two_task" in written and os.path.exists(written["two_task"])

    assert os.path.commonpath([written["matrix"], os.path.join(base_dir, "reliability")]) == os.path.join(
        base_dir, "reliability"
    )

    # Verify existing one-task and two-task artifacts were not modified.
    with open(one_task_scorecard, "r", encoding="utf-8") as f:
        after_one = f.read()
    with open(two_task_summary, "r", encoding="utf-8") as f:
        after_two = f.read()

    assert after_one == before_one
    assert after_two == before_two

    # Validate the reliability matrix fields and expected counts.
    with open(written["matrix"], "r", encoding="utf-8") as f:
        matrix = json.load(f)

    # Expected presence of both lanes
    assert "one_task" in matrix
    assert "two_task" in matrix

    # Check required fields presence
    for lane in ("one_task", "two_task"):
        lane_data = matrix[lane]
        assert "run_count" in lane_data
        assert "retry_total" in lane_data
        assert "failure_family_counts" in lane_data
        assert "supervision_rate" in lane_data
        assert "admission_block_count" in lane_data
        assert "compatibility_regression_count" in lane_data

    # Check computed values for one_task lane
    one = matrix["one_task"]
    assert one["run_count"] == 3
    assert one["green_count"] == 2
    assert one["retry_total"] == 6  # 1 + 2 + 3
    assert one["admission_block_count"] == 1
    assert one["compatibility_regression_count"] == 1
    assert one["failure_family_counts"]["ADMISSION"] == 2
    assert one["failure_family_counts"]["COMPATIBILITY"] == 1
    # Supervision events are 2/3
    assert one["supervision_events"] == 2
    assert abs(one["supervision_rate"] - (2 / 3)) < 1e-3

    # Cross-check lane-specific files contain consistent data.
    with open(written["one_task"], "r", encoding="utf-8") as f:
        one_task_payload = json.load(f)
    with open(written["two_task"], "r", encoding="utf-8") as f:
        two_task_payload = json.load(f)

    assert one_task_payload["run_count"] == one["run_count"]
    assert two_task_payload["run_count"] == matrix["two_task"]["run_count"]

    # The artifact set should be additive and separate
    assert os.path.basename(written["one_task"]) == "one_task_reliability.json"
    assert os.path.basename(written["two_task"]) == "two_task_reliability.json"
    assert os.path.basename(written["matrix"]) == "reliability_matrix.json"


def test_build_reliability_matrix_minimal_shapes():
    # Tolerates empty inputs with deterministic outputs.
    matrix = build_reliability_matrix()
    assert matrix["one_task"]["run_count"] == 0
    assert matrix["one_task"]["supervision_rate"] == 0.0
    assert matrix["two_task"]["run_count"] == 0
    assert matrix["two_task"]["supervision_rate"] == 0.0


def test_reliability_resume_gate_and_checkpoint(tmp_path):
    base_dir = str(tmp_path)

    # Construct a matrix with conservative but acceptable rates under defaults
    one_task_runs: List[Dict] = [
        {"status": "green", "retries": 1, "supervised": False, "admission_blocked": False, "compatibility_regression": False},
        {"status": "green", "retries": 2, "supervised": True, "admission_blocked": False, "compatibility_regression": False},
        {"status": "red", "retries": 1, "supervised": False, "admission_blocked": False, "compatibility_regression": False},
    ]
    two_task_sessions: List[Dict] = [
        {"status": "green", "retries": 2, "supervised": True, "admission_blocked": False, "compatibility_regression": False},
        {"status": "green", "retries": 1, "supervised": False, "admission_blocked": False, "compatibility_regression": False},
        {"status": "red", "retries": 2, "supervised": False, "admission_blocked": False, "compatibility_regression": False},
    ]

    matrix = build_reliability_matrix(one_task_runs=one_task_runs, two_task_sessions=two_task_sessions)

    # Evaluate without a previous snapshot; verdict should be conservative: conditional_under_supervision
    evaluation = evaluate_reliability_resume_gate(matrix)
    assert evaluation["verdict"] in {"conditional_under_supervision", "not_ready"}
    # With the chosen inputs, supervision rates are within default thresholds, so expect conditional readiness
    assert evaluation["verdict"] == "conditional_under_supervision"
    assert "evaluated_metrics" in evaluation
    assert "policy" in evaluation
    assert evaluation["policy"]["broad_unattended_multi_task_autonomy"] == "blocked"

    # Persist the checkpoint
    path = write_reliability_checkpoint(base_dir, evaluation, matrix_snapshot=matrix)
    assert os.path.exists(path)

    payload = json.loads(open(path, "r", encoding="utf-8").read())
    assert payload["checkpoint_kind"] == "post_reliability_resume_gate"
    assert payload["evaluation"]["verdict"] == "conditional_under_supervision"
    assert "matrix" in payload
