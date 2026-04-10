from pathlib import Path


def test_benchmark_module_wires_strict_scorecard_into_live_session_flow() -> None:
    text = Path("src/builder/orchestrator/benchmark.py").read_text(encoding="utf-8")

    assert "from builder.orchestrator.benchmark_scorecard import BenchmarkSession as StrictBenchmarkSession" in text
    assert "strict_session = StrictBenchmarkSession(root)" in text
    assert "for result in session.tasks:" in text
    assert "strict_session.record_run(" in text
    assert "strict_session.close()" in text
