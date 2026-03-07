from tradingbot.strategy.types import Candidate
from tradingbot.execution.types import OrderIntent
from tradingbot.portfolio.types import AccountState, PositionState
from tradingbot.config.settings import Settings
from tradingbot.planner.sizing import PositionSizer

class IntentPlanner:
    @staticmethod
    def build_intents(candidates: list[Candidate], account: AccountState, positions: list[PositionState], cfg: Settings) -> list[OrderIntent]:
        intents = []
        position_sizer = PositionSizer()

        for candidate in candidates:
            qty = position_sizer.size_candidate(candidate, account, positions, cfg)
            if qty > 0:
                intents.append(OrderIntent(symbol=candidate.symbol, qty=qty, side="buy"))

        return intents
