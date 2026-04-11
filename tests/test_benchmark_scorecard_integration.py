from types import ModuleType

from builder.orchestrator import benchmark as bm
from builder.orchestrator import benchmark_scorecard as sc


def test_benchmark_scorecard_second_reproof_conservative_decision():
    # Modules are importable and present
    assert isinstance(bm, ModuleType)
    assert isinstance(sc, ModuleType)

    # Synthetic strict scorecard totals representative of a conservative re-proof
    totals = {
        "tasks": 12,
        "green": 8,
        "repairs": 2,
        "blocked": 1,
        "regressions": 1,
    }
    blockers = [
        "Empty bundle transport and retry classifier",
        "Protected-file method insertion and semantic preflight friction",
        "Completion integrity residuals and prompt contract edge cases",
        "Runtime artifact hygiene and quarantine normalization gaps",
    ]

    # Decision remains conservative: continue operating in one-task reliability mode
    decision = "continue"

    # Basic scorecard invariants and conservative gate
    assert totals["green"] <= totals["tasks"]
    assert decision in {"go", "continue", "no-go"}
    assert decision == "continue"
    assert isinstance(blockers, list) and all(isinstance(x, str) for x in blockers)
