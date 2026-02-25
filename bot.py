import os
from dotenv import load_dotenv

def main():
    load_dotenv()  # loads .env locally; on servers env vars just exist

    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_API_SECRET")
    base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    mode = os.getenv("TRADING_MODE", "paper")

    if not key or not secret:
        raise SystemExit("Missing ALPACA_API_KEY / ALPACA_API_SECRET (set env vars or .env)")

    print(f"TradingBot starting. mode={mode} base_url={base_url}")
    # TODO: initialize Alpaca client + trading loop

if __name__ == "__main__":
    main()
