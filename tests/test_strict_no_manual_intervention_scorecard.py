from agents.lib.scorecard import StrictScorecard


def test_manual_edit_invalidates_autonomous_success(tmp_path):
    sc = StrictScorecard()

    # Four runs: two direct, two self-healed; two with human intervention
    sc.record_run("r1", "direct_completion", manual_intervention=True)   # invalidated
    sc.record_run("r2", "direct_completion", manual_intervention=False)  # counts
    sc.record_run("r3", "self_healed_completion", manual_intervention=True)   # invalidated
    sc.record_run("r4", "self_healed_completion", manual_intervention=False)  # counts

    # Raw totals
    assert sc.total_runs() == 4
    assert sc.direct_completions() == 2
    assert sc.self_healed_completions() == 2

    # Strict autonomous successes exclude manual intervention
    assert sc.strict_autonomous_successes() == 2
    assert sc.invalidated_by_human() == 2

    # Pass rate comparisons
    assert sc.pass_rate() == 1.0  # legacy (raw) pass-rate
    assert sc.pass_rate_strict() == 0.5  # strict pass-rate

    # Durable artifact
    out = tmp_path / "strict_scorecard.json"
    sc.save(str(out))
    data = out.read_text(encoding="utf-8")
    assert '"invalidated_by_human": 2' in data
    assert '"pass_rate": 1.0' in data  # legacy top-level alias
    # strict pass rate appears under "strict"
    assert '"strict"' in data


def test_tracks_direct_and_self_healed_separately():
    sc = StrictScorecard()
    sc.record_run("a", "direct_completion")
    sc.record_run("b", "self_healed_completion")
    sc.record_run("c", "failed")
    sc.record_run("d", "supervised")
    sc.record_run("e", "authority_blocked")
    sc.mark_manual_intervention("e")  # human touched e, but it's authority-blocked already

    assert sc.total_runs() == 5
    assert sc.direct_completions() == 1
    assert sc.self_healed_completions() == 1
    assert sc.failed_runs() == 1
    assert sc.supervised_runs() == 1
    assert sc.authority_blocked_runs() == 1
    assert sc.invalidated_by_human() == 1

    # Strict successes only include direct or self-healed without manual edits
    assert sc.strict_autonomous_successes() == 2
