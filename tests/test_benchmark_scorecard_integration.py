from __future__ import annotations

import json
from pathlib import Path

from builder.orchestrator.benchmark import run_one_task_external_safe_benchmark, run_two_task_canary_benchmark
from builder.orchestrator.benchmark_scorecard import BenchmarkSession as StrictBenchmarkSession


def test_manual_edit_during_run_invalidates_autonomous_success(tmp_path: Path) -> None:
    session_dir = tmp_path / "session_manual_invalidation"
    session = StrictBenchmarkSession(session_dir)

    # Direct completion but with manual edit => not counted as autonomous success
    session.record_run(direct_completion=True, manual_edit=True)
    # A truly direct autonomous completion
    session.record_run(direct_completion=True, manual_edit=False)

    session.close()

    scorecard = json.loads((session_dir / "scorecard.json").read_text(encoding="utf-8"))
    scoreboard = json.loads((session_dir / "scoreboard.json").read_text(encoding="utf-8"))
    promotion = json.loads((session_dir / "promotion.json").read_text(encoding="utf-8"))

    assert scorecard["total_runs"] == 2
    assert scorecard["direct_completions"] == 1
    assert scorecard["self_healed_completions"] == 0
    assert scorecard["invalidated_by_human_intervention"] == 1
    # Only the non-invalidated run is counted as success
    assert scorecard["successes"] == 1
    assert scorecard["failures"] == 1
    assert 0.49 < scorecard["pass_rate"] < 0.51  # 1/2

    # Legacy surface parity with richer fields preserved
    assert scoreboard["total"] == 2
    assert scoreboard["successes"] == 1
    assert scoreboard["direct_completions"] == 1
    assert scoreboard["self_healed_completions"] == 0

    # Promotion artifact with explicit thresholds and a verdict exists
    assert "thresholds" in promotion
    assert "metrics" in promotion
    assert promotion["metrics"]["total_runs"] == 2
    # With pass_rate at 0.5 < min_pass_rate, verdict is not ready
    assert promotion["verdict"] == "not_ready"


def test_direct_and_self_healed_tracked_separately(tmp_path: Path) -> None:
    session_dir = tmp_path / "session_separation"
    session = StrictBenchmarkSession(session_dir)

    session.record_run(direct_completion=True)
    session.record_run(self_healed_completion=True)

    session.close()

    scorecard = json.loads((session_dir / "scorecard.json").read_text(encoding="utf-8"))
    promotion = json.loads((session_dir / "promotion.json").read_text(encoding="utf-8"))

    assert scorecard["total_runs"] == 2
    assert scorecard["direct_completions"] == 1
    assert scorecard["self_healed_completions"] == 1
    assert scorecard["successes"] == 2
    assert scorecard["failures"] == 0
    assert abs(scorecard["pass_rate"] - 1.0) < 1e-9

    # With direct_rate == self_healed_rate and pass_rate high, verdict should be conditional
    assert promotion["verdict"] == "conditionally_ready_under_supervision"


def test_benchmark_harness_writes_strict_scorecard_and_invalidates_manual_intervention(tmp_path: Path) -> None:
    # Two tasks: one manual edit invalidates, one autonomous direct success
    tasks = [{"id": "t1"}, {"id": "t2"}]

    def executor(spec: dict[str, object]) -> dict[str, object]:
        # Always report a direct completion status
        return {"completed": True, "self_heal_used": False}

    # First run: invalidated due to manual intervention
    art1 = run_one_task_external_safe_benchmark(
        tasks=[tasks[0]],
        artifacts_root=tmp_path / "bench1",
        executor=executor,
        manual_intervention=True,
    )
    assert art1.summary["total"] == 1
    assert art1.summary["manual_intervention"] == 1

    # Second run: autonomous direct completion
    art2 = run_one_task_external_safe_benchmark(
        tasks=[tasks[1]],
        artifacts_root=tmp_path / "bench2",
        executor=executor,
        manual_intervention=False,
    )
    assert art2.summary["completed_direct"] == 1

    # Check strict scorecard artifacts
    score1 = json.loads((tmp_path / "bench1" / "scorecard.json").read_text(encoding="utf-8"))
    score2 = json.loads((tmp_path / "bench2" / "scorecard.json").read_text(encoding="utf-8"))

    assert score1["total_runs"] == 1
    assert score1["invalidated_by_human_intervention"] == 1
    assert score1["successes"] == 0
    assert score1["failures"] == 1

    assert score2["total_runs"] == 1
    assert score2["direct_completions"] == 1
    assert score2["successes"] == 1
    assert score2["failures"] == 0

    # Promotion artifacts and verdicts
    promo1 = json.loads((tmp_path / "bench1" / "promotion.json").read_text(encoding="utf-8"))
    promo2 = json.loads((tmp_path / "bench2" / "promotion.json").read_text(encoding="utf-8"))

    assert promo1["verdict"] == "not_ready"
    assert promo2["verdict"] == "ready_to_be_default"


def test_two_task_canary_benchmark_persists_metrics_and_trials(tmp_path: Path) -> None:
    tasks = [{"id": "A"}, {"id": "B"}, {"id": "C"}, {"id": "D"}, {"id": "E"}]

    def executor(spec: dict[str, object]) -> dict[str, object]:
        tid = spec["id"]
        if tid == "A":
            return {"eligible_for_pilot": True, "admitted": True, "completed": True, "handoff_status": "", "supervised": False}
        if tid == "B":
            return {"eligible_for_pilot": True, "admitted": False, "blocked_admission": True, "completed": False, "handoff_status": "", "supervised": False}
        if tid == "C":
            return {"eligible_for_pilot": False, "admitted": False, "completed": False, "handoff_status": "", "supervised": False}
        if tid == "D":
            return {"eligible_for_pilot": True, "admitted": True, "completed": False, "handoff_status": "incomplete", "supervised": True}
        if tid == "E":
            return {"eligible_for_pilot": True, "admitted": True, "completed": False, "handoff_status": "incompatible", "supervised": False}
        return {}

    run_two_task_canary_benchmark(tasks, artifacts_root=tmp_path / "canary", executor=executor)
