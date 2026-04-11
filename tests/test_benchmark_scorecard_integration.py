from __future__ import annotations

import json
from pathlib import Path

from builder.orchestrator.benchmark_scorecard import open_session


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_manual_edit_invalidates_autonomous_success(tmp_path: Path) -> None:
    sess = open_session(tmp_path)
    # This run would otherwise be a direct completion, but a manual edit invalidates it.
    sess.record_run(direct_completion=True, manual_edit=True)
    sess.close()

    scorecard_path = tmp_path / "scorecard.json"
    assert scorecard_path.exists(), "Integrated scorecard must be written through the benchmark path"

    data = load_json(scorecard_path)
    assert data["total_runs"] == 1
    assert data["invalidated_by_human_intervention"] == 1
    # Not counted as an autonomous success
    assert data["direct_completions"] == 0
    assert data["self_healed_completions"] == 0
    # Pass-rate compatibility: invalidated run treated as failure
    assert data["successes"] == 0
    assert data["failures"] == 1
    assert data["pass_rate"] == 0.0


def test_direct_and_self_healed_counted_separately(tmp_path: Path) -> None:
    sess = open_session(tmp_path)
    sess.record_run(direct_completion=True)
    sess.record_run(self_healed_completion=True)
    sess.close()

    data = load_json(tmp_path / "scorecard.json")
    assert data["total_runs"] == 2
    assert data["direct_completions"] == 1
    assert data["self_healed_completions"] == 1
    assert data["successes"] == 2
    assert data["failures"] == 0
    assert data["pass_rate"] == 1.0


def test_integrated_artifacts_written_in_session_dir(tmp_path: Path) -> None:
    sess = open_session(tmp_path)
    sess.record_run(direct_completion=True)
    sess.record_run(failed=True)
    sess.record_run(authority_blocked=True)
    sess.record_run(supervised=True)
    sess.record_run(self_healed_completions=True) if False else None  # no-op to keep signature stable
    sess.record_run(self_healed_completion=True, manual_edit=True)  # invalidated
    sess.close()

    # Strict integrated scorecard
    scorecard_path = tmp_path / "scorecard.json"
    assert scorecard_path.exists()

    # Preserve compatibility with pass-rate scoreboard
    scoreboard_path = tmp_path / "scoreboard.json"
    assert scoreboard_path.exists()

    scorecard = load_json(scorecard_path)
    scoreboard = load_json(scoreboard_path)

    # Totals align
    assert scorecard["total_runs"] == 5
    assert scoreboard["total"] == 5

    # Scoreboard pass-rate surface matches strict scorecard derived values
    assert scoreboard["successes"] == scorecard["successes"]
    assert scoreboard["failures"] == scorecard["failures"]
    assert scoreboard["pass_rate"] == scorecard["pass_rate"]

    # Category breakdowns present in strict scorecard
    assert scorecard["authority_blocked_runs"] == 1
    assert scorecard["supervised_runs"] == 1
    assert scorecard["invalidated_by_human_intervention"] == 1
