from __future__ import annotations

from agents import run_task


def test_parse_completion_integrity_directives() -> None:
    task = (
        "## Completion Integrity Gate\n"
        "- REQUIRE_EXISTING_TOUCH: src/builder/orchestrator/benchmark.py\n"
        "- MIN_EXISTING_NONTEST_TOUCHES: 1\n"
        "- ALLOW_HELPER_ONLY: false\n"
    )
    parsed = run_task.parse_completion_integrity_directives(task)
    assert parsed == {
        "required_existing_touches": ["src/builder/orchestrator/benchmark.py"],
        "min_existing_nontest_touches": 1,
        "allow_helper_only": False,
    }


def test_completion_integrity_rejects_helper_only_integration_bundle() -> None:
    task = "Integrate the benchmark scorecard into the live harness.\n"
    bundle = {
        "src/builder/orchestrator/benchmark_scorecard.py": "x = 1\n",
        "tests/test_benchmark_scorecard_integration.py": "def test_ok():\n    assert True\n",
    }
    ok, msg = run_task.evaluate_completion_integrity_gate(task, bundle, baseline={}, required_paths=list(bundle))
    assert ok is False
    assert "helper-only" in msg or "existing non-test/doc integration surface" in msg


def test_completion_integrity_accepts_existing_surface_touch() -> None:
    task = "Integrate the benchmark scorecard into the live harness.\n"
    bundle = {
        "src/builder/orchestrator/benchmark.py": "updated\n",
        "src/builder/orchestrator/benchmark_scorecard.py": "new helper\n",
    }
    baseline = {"src/builder/orchestrator/benchmark.py": "old\n"}
    ok, msg = run_task.evaluate_completion_integrity_gate(task, bundle, baseline=baseline, required_paths=list(bundle))
    assert ok is True
    assert msg == ""


def test_completion_integrity_requires_declared_existing_surface() -> None:
    task = (
        "## Completion Integrity Gate\n"
        "- REQUIRE_EXISTING_TOUCH: src/builder/orchestrator/benchmark.py\n"
        "- ALLOW_HELPER_ONLY: false\n"
    )
    bundle = {"src/builder/orchestrator/benchmark_scorecard.py": "new helper\n"}
    ok, msg = run_task.evaluate_completion_integrity_gate(task, bundle, baseline={}, required_paths=list(bundle))
    assert ok is False
    assert "required existing integration surfaces were not touched" in msg
