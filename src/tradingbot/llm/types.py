from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class LLMDecision:
    """Decision returned by the LLM advisor.

    action meanings:
      - approve: candidate is allowed to proceed
      - veto: candidate must be removed
      - no_trade: advisor is uncertain; treat as do-not-trade for v1
    """

    symbol: str
    action: Literal["approve", "veto", "no_trade"]
    reason: str
