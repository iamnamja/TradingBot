from dataclasses import dataclass

@dataclass
class AccountState:
    cash_usd: float
    equity_usd: float
    buying_power_usd: float

@dataclass
class PositionState:
    symbol: str
    qty: float
    market_value_usd: float
