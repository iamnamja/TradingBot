from datetime import datetime, timezone
from tradingbot.data.client import DataClient
from tradingbot.execution.engine import ExecutionEngine
from tradingbot.llm.advisor import LLMAdvisor
from tradingbot.risk.risk_gate import RiskGate
from tradingbot.strategy.strategy_v1 import StrategyV1
from tradingbot.config.settings import Settings
from tradingbot.logging.audit import write_audit

class CycleRunner:
    def __init__(self, data_client: DataClient, llm_advisor: LLMAdvisor, risk_gate: RiskGate, execution_engine: ExecutionEngine, settings: Settings):
        self.data_client = data_client
        self.llm_advisor = llm_advisor
        self.risk_gate = risk_gate
        self.execution_engine = execution_engine
        self.settings = settings

    def run_once(self) -> dict:
        timestamp = datetime.now(timezone.utc)
        audit_event = {
            "timestamp": timestamp.isoformat(),
            "market_hours_guard": {},
            "candidates": [],
            "llm_decisions": [],
            "risk_decisions": [],
            "executed_intents": [],
            "errors": []
        }

        # Check market hours
        is_open, reason = self.check_market_hours()
        audit_event["market_hours_guard"] = {"is_open": is_open, "reason": reason}
        if not is_open:
            return audit_event

        # Fetch data
        candidates = StrategyV1.generate(self.settings.symbols, self.data_client, self.settings)
        audit_event["candidates"] = [candidate.symbol for candidate in candidates]

        # LLM approval/veto
        decisions = self.llm_advisor.review(candidates, context={})
        audit_event["llm_decisions"] = [{"symbol": decision.symbol, "action": decision.action, "reason": decision.reason} for decision in decisions]

        # Risk gate evaluation
        for candidate in candidates:
            allowed, reason = self.risk_gate.evaluate(candidate, {}, self.settings)
            audit_event["risk_decisions"].append({"symbol": candidate.symbol, "allowed": allowed, "reason": reason})

        # Execute or dry-run
        intents = []  # Prepare intents based on candidates and decisions
        if self.settings.effective_dry_run:
            audit_event["executed_intents"] = [{"symbol": candidate.symbol, "action": "dry-run"} for candidate in candidates]
        else:
            results = self.execution_engine.execute(intents, {}, self.settings)
            audit_event["executed_intents"] = results

        # Write audit log
        audit_path = write_audit(audit_event)
        return {"audit_path": audit_path}

    def check_market_hours(self):
        # Placeholder for actual market hours check logic
        return True, "market open"
