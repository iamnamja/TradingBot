import os
import time
from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


def get_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def main() -> None:
    load_dotenv()

    api_key = get_env("ALPACA_API_KEY")
    api_secret = get_env("ALPACA_API_SECRET")
    paper = os.getenv("ALPACA_PAPER", "true").lower() in ("1", "true", "yes", "y")
    dry_run = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes", "y")

    print(f"TradingBot starting... mode={'paper' if paper else 'live'} dry_run={dry_run}")

    trading = TradingClient(api_key, api_secret, paper=paper)

    acct = trading.get_account()
    print("Account:")
    print(f"  status:      {acct.status}")
    print(f"  cash:        {acct.cash}")
    print(f"  equity:      {acct.equity}")
    print(f"  buyingPower: {acct.buying_power}")

    symbol = "SPY"
    qty = 1

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

        # Give it a moment, then re-check status
        time.sleep(2)
        refreshed = trading.get_order_by_id(order.id)
        print("Order refreshed:")
        print(f"  status:         {refreshed.status}")
        print(f"  filled_qty:     {refreshed.filled_qty}")
        print(f"  filled_avg_px:  {refreshed.filled_avg_price}")

    # Show positions
    positions = trading.get_all_positions()
    print("\nPositions:")
    if not positions:
        print("  (none)")
    else:
        for p in positions:
            print(f"  {p.symbol}: qty={p.qty} avg_entry={p.avg_entry_price} unrealized_pl={p.unrealized_pl}")


if __name__ == "__main__":
    main()