import time

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from tradingbot.config.settings import load_settings, print_startup_summary

# NEW (Task 007 wiring)
from tradingbot.llm.noop import NoopLLMAdvisor


def main() -> None:
    s = load_settings()
    print_startup_summary(s)

    # NEW (Task 007 wiring)
    if s.llm_enabled:
        # v1: still use noop until a real advisor is added
        print("LLM advisor: ENABLED (using NoopLLMAdvisor for now)")
    else:
        print("LLM advisor: DISABLED (using NoopLLMAdvisor)")
        
    _llm_advisor = NoopLLMAdvisor()

    api_key = s.env.alpaca_api_key
    api_secret = s.env.alpaca_api_secret
    if not api_key or not api_secret:
        raise RuntimeError(
            "Missing Alpaca credentials. Set TRADINGBOT_ALPACA_API_KEY and "
            "TRADINGBOT_ALPACA_API_SECRET in .env (recommended) or env vars."
        )

    paper = s.effective_mode == "paper"
    dry_run = s.effective_dry_run

    trading = TradingClient(api_key, api_secret, paper=paper)

    acct = trading.get_account()
    print("Account:")
    print(f"  status:      {acct.status}")
    print(f"  cash:        {acct.cash}")
    print(f"  equity:      {acct.equity}")
    print(f"  buyingPower: {acct.buying_power}")

    symbol = (s.symbols[0] if s.symbols else "SPY")
    qty = 1

    # (Optional) Example of where it will be used later:
    # candidates = [...]  # deterministic strategy output
    # decisions = _llm_advisor.review(candidates, context={"account": {"equity": acct.equity}})
    # ... filter candidates based on decisions ...

    if dry_run:
        print(f"[DRY_RUN] Would submit market BUY: {qty} {symbol}")
    else:
        order_req = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        order = trading.submit_order(order_req)
        print("Order submitted:")
        print(f"  order_id: {order.id}")
        print(f"  status:   {order.status}")

        time.sleep(2)
        refreshed = trading.get_order_by_id(order.id)
        print("Order refreshed:")
        print(f"  status:         {refreshed.status}")
        print(f"  filled_qty:     {refreshed.filled_qty}")
        print(f"  filled_avg_px:  {refreshed.filled_avg_price}")

    positions = trading.get_all_positions()
    print("\nPositions:")
    if not positions:
        print("  (none)")
    else:
        for p in positions:
            print(
                f"  {p.symbol}: qty={p.qty} avg_entry={p.avg_entry_price} "
                f"unrealized_pl={p.unrealized_pl}"
            )


if __name__ == "__main__":
    main()
