from tradingbot.data.client import DataClient
from tradingbot.config.settings import Settings
from tradingbot.indicators import sma, trend_up
from tradingbot.strategy.types import Candidate

class StrategyV1:
    @staticmethod
    def generate(symbols: list[str], data: DataClient, cfg: Settings) -> list[Candidate]:
        candidates = []
        for symbol in symbols:
            bars = data.get_bars(symbol)
            if len(bars) < 20:
                continue
            
            last_close = bars[-1]['close']
            closes = [bar['close'] for bar in bars]
            sma20 = sma(closes, 20)[-1]
            is_trend_up = trend_up(closes, lookback=5)

            if last_close > sma20 and is_trend_up:
                score = (last_close - sma20) / sma20
                reason = f"Last close {last_close} is above SMA(20) {sma20} and trend is up."
                snapshot = {
                    'last_close': last_close,
                    'sma20': sma20,
                    'trend_up': is_trend_up,
                }
                candidates.append(Candidate(symbol=symbol, score=score, reason=reason, snapshot=snapshot))
        
        return candidates
