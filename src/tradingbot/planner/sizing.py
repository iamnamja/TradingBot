from math import floor
from tradingbot.strategy.types import Candidate
from tradingbot.portfolio.types import AccountState, PositionState
from tradingbot.config.settings import Settings

class PositionSizer:
    @staticmethod
    def size_candidate(candidate: Candidate, account: AccountState, positions: list[PositionState], cfg: Settings) -> int:
        last_close = candidate.snapshot.get("last_close")
        if last_close is None or not isinstance(last_close, (int, float)) or last_close <= 0:
            return 0

        target_notional = cfg.max_position_size_usd if hasattr(cfg, 'max_position_size_usd') else 0
        qty = floor(target_notional / last_close)

        if qty < 1:
            return 0
        return qty
