from typing import List, Dict
from tradingbot.config.settings import Settings
from tradingbot.brokers.base import Broker
from tradingbot.execution.types import OrderIntent

class ExecutionEngine:
    def execute(self, intents: List[OrderIntent], broker: Broker, cfg: Settings) -> List[Dict]:
        results = []
        for intent in intents:
            if cfg.effective_dry_run:
                print(f"[DRY_RUN] Would submit order: {intent.side} {intent.qty} of {intent.symbol}")
                results.append({"symbol": intent.symbol, "qty": intent.qty, "side": intent.side, "status": "dry_run"})
            else:
                try:
                    result = broker.submit_order(intent.symbol, intent.qty, intent.side)
                    results.append(result)
                except Exception as e:
                    results.append({"symbol": intent.symbol, "qty": intent.qty, "side": intent.side, "status": "error", "message": str(e)})
        return results
