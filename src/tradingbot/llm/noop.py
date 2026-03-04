from __future__ import annotations

from typing import Any

from .advisor import LLMAdvisor
from .types import LLMDecision


class NoopLLMAdvisor(LLMAdvisor):
    """No-op advisor: approves everything.

    Used when llm_enabled is False or during tests.
    """

    def review(self, candidates: list[Any], context: dict[str, Any]) -> list[LLMDecision]:
        decisions: list[LLMDecision] = []
        for c in candidates:
            symbol = getattr(c, "symbol", None) or getattr(c, "ticker", None) or str(c)
            decisions.append(LLMDecision(symbol=str(symbol), action="approve", reason="noop: approve"))
        return decisions
