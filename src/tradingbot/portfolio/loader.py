from tradingbot.portfolio.types import AccountState, PositionState

class PortfolioStateLoader:
    def __init__(self, broker):
        self.broker = broker

    def load(self) -> tuple[AccountState, list[PositionState]]:
        account_summary = self.broker.get_account()
        positions = self.broker.get_all_positions()

        account_state = AccountState(
            cash_usd=float(account_summary.cash),
            equity_usd=float(account_summary.equity),
            buying_power_usd=float(account_summary.buying_power),
        )

        position_states = [
            PositionState(
                symbol=p.symbol,
                qty=float(p.qty),
                market_value_usd=float(p.market_value),
            )
            for p in positions
        ]

        return account_state, position_states
