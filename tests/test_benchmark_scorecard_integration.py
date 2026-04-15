from __future__ import annotations

import json
import sys
import types
from pathlib import Path

from builder.orchestrator.benchmark import run_one_task_external_safe_benchmark, run_two_task_canary_benchmark
from builder.orchestrator.benchmark_scorecard import BenchmarkSession as StrictBenchmarkSession
from builder.orchestrator.bounded_corpus_benchmark import run_bounded_two_task_corpus_benchmark


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

    score_path = tmp_path / "canary" / "canary_scorecard.json"
    promo_path = tmp_path / "canary" / "canary_promotion.json"
    trials_path = tmp_path / "canary" / "canary_trials.json"

    assert score_path.exists()
    assert promo_path.exists()
    assert trials_path.exists()

    score = json.loads(score_path.read_text(encoding="utf-8"))
    metrics = score["metrics"]
    assert metrics["total"] == 5
    assert metrics["pilot_attempts"] == 4
    assert metrics["ineligible_attempts"] == 1
    assert metrics["admissions_blocked"] == 1
    assert metrics["pilot_completions"] == 1
    assert metrics["handoff_incomplete_failures"] == 1
    assert metrics["handoff_incompatible_failures"] == 1
    assert metrics["supervised_interventions"] == 1

    promo = json.loads(promo_path.read_text(encoding="utf-8"))
    assert "verdict" in promo
    assert "thresholds" in promo
    assert promo["metrics"]["pilot_attempts"] == 4

    trials = json.loads(trials_path.read_text(encoding="utf-8"))
    assert len(trials) == 5
    by_id = {t["task_id"]: t for t in trials}
    assert by_id["B"]["blocked_admission"] is True
    assert by_id["C"]["eligible_for_pilot"] is False
    assert by_id["D"]["handoff_status"] == "incomplete"
    assert by_id["D"]["supervised"] is True
    assert by_id["E"]["handoff_status"] == "incompatible"


def test_canary_does_not_modify_strict_one_task_artifacts(tmp_path: Path) -> None:
    def executor_canary(_spec: dict[str, object]) -> dict[str, object]:
        return {"eligible_for_pilot": True, "admitted": True, "completed": True, "handoff_status": "", "supervised": False}

    def executor_strict(_spec: dict[str, object]) -> dict[str, object]:
        return {"completed": True, "self_heal_used": False}

    # Write strict artifacts separately
    run_one_task_external_safe_benchmark(
        tasks=[{"id": "strict1"}],
        artifacts_root=tmp_path / "strict_session",
        executor=executor_strict,
        manual_intervention=False,
    )

    # Canary writes only canary_* artifacts
    run_two_task_canary_benchmark(
        tasks=[{"id": "p1"}, {"id": "p2"}],
        artifacts_root=tmp_path / "canary_session",
        executor=executor_canary,
    )

    strict_root = tmp_path / "strict_session"
    canary_root = tmp_path / "canary_session"

    # One-task strict artifacts exist for strict session
    assert (strict_root / "scorecard.json").exists()
    assert (strict_root / "scoreboard.json").exists()
    assert (strict_root / "promotion.json").exists()

    # Canary session should not contain strict one-task artifacts
    assert not (canary_root / "scorecard.json").exists()
    assert not (canary_root / "scoreboard.json").exists()
    assert not (canary_root / "promotion.json").exists()
    # But must contain canary artifacts
    assert (canary_root / "canary_scorecard.json").exists()
    assert (canary_root / "canary_promotion.json").exists()
    assert (canary_root / "canary_trials.json").exists()


def test_bounded_corpus_benchmark_writes_promotion_artifact(tmp_path: Path, monkeypatch) -> None:
    # Inject a fake bounded pilot runner to avoid external dependencies during tests.
    mod = types.ModuleType("agents.lib.bounded_pilot")

    def _fake_runner(pair: dict[str, object], session_dir: str | None = None) -> dict[str, object]:
        pid = pair.get("id")
        if pid == "p1":
            return {"admitted": True, "completed": True, "handoff_failure": False, "supervised_intervention": False}
        if pid == "p2":
            return {"admitted": True, "completed": False, "handoff_failure": True, "supervised_intervention": True}
        return {"admitted": False, "completed": False, "handoff_failure": False, "supervised_intervention": False, "status": "blocked"}

    setattr(mod, "run_bounded_two_task_pilot", _fake_runner)
    sys.modules["agents.lib.bounded_pilot"] = mod

    pairs = [
        {"id": "p1", "eligible": True},
        {"id": "p2", "eligible": True},
        {"id": "p3", "eligible": False},
    ]

    summary = run_bounded_two_task_corpus_benchmark(session_dir=str(tmp_path), pairs=pairs)
    artifacts_dir = Path(summary["artifacts_dir"])

    assert (artifacts_dir / "pairs.json").exists()
    assert (artifacts_dir / "summary.json").exists()
    assert (artifacts_dir / "bounded_corpus_promotion.json").exists()

    promo = json.loads((artifacts_dir / "bounded_corpus_promotion.json").read_text(encoding="utf-8"))
    assert "verdict" in promo
    assert "thresholds" in promo
    assert "metrics" in promo
    assert "widening_checkpoint" in promo
    assert promo["metrics"]["total_pairs"] == 3
    assert promo["widening_checkpoint"]["broad_unattended_multi_task_autonomy_blocked"] is True
    assert promo["widening_checkpoint"]["standalone_orchestrator_productization_blocked"] is True


def test_empty_output_regression_guard_degrades_promotion_when_threshold_exceeded(tmp_path: Path) -> None:
    # Single direct-success task
    tasks = [{"id": "guard1"}]

    def executor(_spec: dict[str, object]) -> dict[str, object]:
        return {"completed": True, "self_heal_used": False}

    # Build a transport corpus with high empty-output rate: 3/10 empty
    transport_records = [
        {"raw_capture_status": "non_empty", "parser_path": "bundle", "success": True, "fallback_applied": False},
        {"raw_capture_status": "empty_zero_length", "parser_path": "bundle", "success": False, "fallback_applied": False},
        {"raw_capture_status": "empty_whitespace_only", "parser_path": "bundle", "success": False, "fallback_applied": True},
        {"raw_capture_status": "non_empty", "parser_path": "bundle", "success": True, "fallback_applied": False},
        {"raw_capture_status": "non_empty", "parser_path": "protected_method", "success": True, "fallback_applied": False},
        {"raw_capture_status": "non_empty", "parser_path": "protected_method", "success": True, "fallback_applied": False},
        {"raw_capture_status": "non_empty", "parser_path": "bundle", "success": True, "fallback_applied": False},
        {"raw_capture_status": "non_empty", "parser_path": "bundle", "success": True, "fallback_applied": False},
        {"raw_capture_status": "empty_zero_length", "parser_path": "bundle", "success": False, "fallback_applied": True},
        {"raw_capture_status": "non_empty", "parser_path": "protected_method", "success": True, "fallback_applied": False},
    ]

    run_one_task_external_safe_benchmark(
        tasks=tasks,
        artifacts_root=tmp_path / "guard_session",
        executor=executor,
        manual_intervention=False,
        transport_records=transport_records,
    )

    # Baseline promotion would be "ready_to_be_default"; with guard triggered, it should be degraded.
    promo = json.loads((tmp_path / "guard_session" / "promotion.json").read_text(encoding="utf-8"))
    assert promo["verdict"] == "not_ready"

    guard = json.loads((tmp_path / "guard_session" / "promotion_guard.json").read_text(encoding="utf-8"))
    assert guard["empty_output"]["guard_triggered"] is True
    assert guard["verdict_baseline"] == "ready_to_be_default"
    assert guard["verdict_with_guard"] == "not_ready"
