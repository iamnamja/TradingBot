from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):  # type: ignore[no-redef]
        return False


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
    # Task 007: LLM advisor toggle. When False, system must not call external APIs.
    llm_enabled: bool = False

    @property
    def effective_mode(self) -> str:
        return self.mode

    @property
    def effective_dry_run(self) -> bool:
        return self.dry_run


def load_settings() -> Settings:
    # Loads variables from .env (if present) into os.environ
    load_dotenv()

    api_key = os.getenv("TRADINGBOT_ALPACA_API_KEY", "").strip()
    api_secret = os.getenv("TRADINGBOT_ALPACA_API_SECRET", "").strip()

    mode = os.getenv("TRADINGBOT_MODE", "paper").strip().lower()
    if mode not in ("paper", "live"):
        raise ValueError("TRADINGBOT_MODE must be 'paper' or 'live'")

    dry_run = _truthy(os.getenv("TRADINGBOT_DRY_RUN", "true"))

    symbols_raw = os.getenv("TRADINGBOT_SYMBOLS", "").strip()
    symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()] if symbols_raw else []

    llm_enabled = _truthy(os.getenv("TRADINGBOT_LLM_ENABLED", "false"))

    return Settings(
        env=Env(alpaca_api_key=api_key, alpaca_api_secret=api_secret),
        mode=mode,
        dry_run=dry_run,
        symbols=symbols,
        llm_enabled=llm_enabled,
    )


def print_startup_summary(s: Settings) -> None:
    sym = ", ".join(s.symbols) if s.symbols else "(none configured)"
    print("Config:")
    print(f"  mode:        {s.mode}")
    print(f"  dry_run:     {s.dry_run}")
    print(f"  symbols:     {sym}")
    print(f"  llm_enabled: {s.llm_enabled}")
