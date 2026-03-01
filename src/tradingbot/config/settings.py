from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv


def _truthy(v: Optional[str]) -> bool:
    if v is None:
        return False
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


@dataclass(frozen=True)
class Env:
    alpaca_api_key: str
    alpaca_api_secret: str


@dataclass(frozen=True)
class Settings:
    env: Env
    mode: str  # "paper" or "live"
    dry_run: bool
    symbols: List[str]

    @property
    def effective_mode(self) -> str:
        return self.mode

    @property
    def effective_dry_run(self) -> bool:
        return self.dry_run


def load_settings() -> Settings:
    load_dotenv()

    api_key = os.getenv("TRADINGBOT_ALPACA_API_KEY", "").strip()
    api_secret = os.getenv("TRADINGBOT_ALPACA_API_SECRET", "").strip()

    mode = os.getenv("TRADINGBOT_MODE", "paper").strip().lower()
    if mode not in ("paper", "live"):
        raise ValueError("TRADINGBOT_MODE must be 'paper' or 'live'")

    dry_run = _truthy(os.getenv("TRADINGBOT_DRY_RUN", "true"))

    symbols_raw = os.getenv("TRADINGBOT_SYMBOLS", "").strip()
    symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()] if symbols_raw else []

    return Settings(
        env=Env(alpaca_api_key=api_key, alpaca_api_secret=api_secret),
        mode=mode,
        dry_run=dry_run,
        symbols=symbols,
    )


def print_startup_summary(s: Settings) -> None:
    sym = ", ".join(s.symbols) if s.symbols else "(none configured)"
    print("Config:")
    print(f"  mode:    {s.mode}")
    print(f"  dry_run: {s.dry_run}")
    print(f"  symbols: {sym}")