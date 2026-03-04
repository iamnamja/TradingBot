from __future__ import annotations

from typing import Any, Protocol

from .types import PortfolioState
from tradingbot.config.settings import Settings


class CandidateLike(Protocol):
    symbol: str


def _candidate_trade_size_usd(candidate: Any) -> float:
    # Support common attribute names.
    if hasattr(candidate, "size_usd"):
        return float(getattr(candidate, "size_usd"))
    if hasattr(candidate, "trade_size_usd"):
        return float(getattr(candidate, "trade_size_usd"))
    if hasattr(candidate, "size"):
        return float(getattr(candidate, "size"))
    if hasattr(candidate, "notional_usd"):
        return float(getattr(candidate, "notional_usd"))
    raise AttributeError("Candidate must have a size attribute (size_usd/size/notional_usd)")


class RiskGate:
    """Simple v1 risk gate.

    Returns (allowed, reason). Reasons are stable strings suitable for logging/auditing.
    """

    def evaluate(self, candidate: CandidateLike, state: PortfolioState, cfg: Settings) -> tuple[bool, str]:
        symbol = str(getattr(candidate, "symbol", "")).upper().strip() or "UNKNOWN"
        trade_size_usd = _candidate_trade_size_usd(candidate)

        # If this would open a NEW position, enforce max_open_positions.
        if symbol not in state.open_positions and len(state.open_positions) >= cfg.max_open_positions:
            return False, "risk denied: max positions reached"

        if trade_size_usd > cfg.max_position_size_usd:
            return False, "risk denied: trade size exceeds max"

        if state.trades_today >= cfg.max_trades_per_day:
            return False, "risk denied: max trades per day"

        return True, "risk ok"
