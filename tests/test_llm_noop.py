from __future__ import annotations

from dataclasses import dataclass

from tradingbot.llm.noop import NoopLLMAdvisor


@dataclass
class DummyCandidate:
    symbol: str


def test_noop_llm_approves_all():
    advisor = NoopLLMAdvisor()
    candidates = [DummyCandidate("AAPL"), DummyCandidate("MSFT"), DummyCandidate("NVDA")]

    decisions = advisor.review(candidates=candidates, context={"foo": "bar"})

    assert len(decisions) == len(candidates)
    for d, c in zip(decisions, candidates, strict=True):
        assert d.symbol == c.symbol
        assert d.action == "approve"
        assert d.reason != ""
