from tradingbot.config.settings import Settings
from tradingbot.risk.types import PortfolioState

class RiskGate:
    def evaluate(self, candidate, state: PortfolioState, cfg: Settings) -> tuple[bool, str]:
        if len(state.open_positions) >= cfg.max_open_positions:
            return False, "risk denied: max positions reached"
        if candidate.size > cfg.max_position_size_usd:
            return False, "risk denied: trade size exceeds max"
        if state.trades_today >= cfg.max_trades_per_day:
            return False, "risk denied: max trades per day"
        return True, "trade allowed"
