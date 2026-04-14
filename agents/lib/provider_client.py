from __future__ import annotations

import os
import re
from typing import Any, Dict, List

from agents.lib.model_profiles import (
    CONTRACT_PATCH_APPLY_MODE,
    CONTRACT_STRICT_FILE_BUNDLE,
    TRANSPORT_FILE_BUNDLE,
    TRANSPORT_PATCH,
    get_model_profile as _profiles_get_model_profile,
    output_transport_from_profile as _profiles_output_transport,
    transport_contract_from_profile as _profiles_transport_contract,
)


_MODEL_VALIDATION_CACHE: Dict[str, set[str]] = {"openai": set(), "anthropic": set()}


def default_provider() -> str:
    return os.getenv("TRADINGBOT_LLM_PROVIDER", "openai").strip().lower()


def default_model_for_provider(provider: str) -> str:
    provider = (provider or "").strip().lower()
    if provider == "openai":
        return os.getenv("TRADINGBOT_OPENAI_MODEL", "gpt-5")
    if provider == "anthropic":
        return os.getenv("TRADINGBOT_ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
    return os.getenv("TRADINGBOT_LLM_MODEL", "gpt-5")


def default_api_mode_for_provider(provider: str) -> str:
    provider = (provider or "").strip().lower()
    if provider == "openai":
        return os.getenv("TRADINGBOT_OPENAI_API_MODE", "").strip().lower() or "responses"
    if provider == "anthropic":
        return os.getenv("TRADINGBOT_ANTHROPIC_API_MODE", "").strip().lower() or "messages"
    return ""


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class NormalizedLLMResponse:
    __slots__ = (
        "text",
        "stop_reason",
        "usage_input_tokens",
        "usage_output_tokens",
        "request_id",
        "raw_provider_response",
    )

    def __init__(
        self,
        text: str,
        stop_reason: str | None = None,
        usage_input_tokens: int | None = None,
        usage_output_tokens: int | None = None,
        request_id: str | None = None,
        raw_provider_response: Any | None = None,
    ) -> None:
        self.text = text
        self.stop_reason = stop_reason
        self.usage_input_tokens = usage_input_tokens
        self.usage_output_tokens = usage_output_tokens
        self.request_id = request_id
        self.raw_provider_response = raw_provider_response


def _join_system_messages(messages: List[dict]) -> str:
    parts: List[str] = []
    for msg in messages:
        role = str(msg.get("role", "")).strip().lower()
        if role in {"system", "developer"}:
            content = str(msg.get("content", "") or "").strip()
            if content:
                parts.append(content)
    return "\n\n".join(parts).strip()


def _non_system_messages(messages: List[dict]) -> List[dict]:
    out: List[dict] = []
    for msg in messages:
        role = str(msg.get("role", "")).strip().lower()
        if role in {"system", "developer"}:
            continue
        content = str(msg.get("content", "") or "")
        out.append({"role": role or "user", "content": content})
    if not out:
        out.append({"role": "user", "content": ""})
    return out


def _messages_to_openai_responses_input(messages: List[dict]) -> List[dict]:
    items: List[dict] = []
    for msg in _non_system_messages(messages):
        role = msg["role"]
        if role not in {"user", "assistant"}:
            role = "user"
        items.append(
            {
                "role": role,
                "content": [{"type": "input_text", "text": msg["content"]}],
            }
        )
    return items


def _extract_retry_after_seconds(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if headers:
        raw = headers.get("retry-after") or headers.get("Retry-After")
        if raw:
            try:
                return float(raw)
            except (TypeError, ValueError):
                pass
    text = str(exc)
    ms_match = re.search(r"try again in\s+([0-9]+)ms", text, re.IGNORECASE)
    if ms_match:
        try:
            return float(ms_match.group(1)) / 1000.0
        except ValueError:
            return None
    s_match = re.search(r"try again in\s+([0-9]+(?:\.[0-9]+)?)s", text, re.IGNORECASE)
    if s_match:
        try:
            return float(s_match.group(1))
        except ValueError:
            return None
    return None


# ---- Explicit model-profile and transport contract helpers ----


def _coerce_provider_model(provider: str | None, model: str | None) -> tuple[str, str]:
    p = (provider or default_provider()).strip().lower()
    m = (model or default_model_for_provider(p)).strip()
    return p, m


def model_profile_for(provider: str | None = None, model: str | None = None) -> Dict[str, object]:
    """
    Resolve the explicit model profile metadata for a given provider/model pair.
    Defaults to the GPT-style strict file-bundle profile.
    """
    p, m = _coerce_provider_model(provider, model)
    return dict(_profiles_get_model_profile(p, m))


def output_transport_for_model(provider: str | None = None, model: str | None = None) -> str:
    """
    Return the expected output transport for the selected model/profile.
    Values: 'file_bundle' (default) or 'patch'.
    """
    profile = model_profile_for(provider, model)
    return _profiles_output_transport(profile)


def transport_contract_for_model(provider: str | None = None, model: str | None = None) -> str:
    """
    Return the expected transport contract token for the selected model/profile.
    Values: 'strict_file_bundle' (default) or 'patch_apply_mode'.
    """
    profile = model_profile_for(provider, model)
    return _profiles_transport_contract(profile)


def declared_transport_contract(provider: str | None = None, model: str | None = None) -> Dict[str, str]:
    """
    Public transport-contract declaration for runner inspection.
    This is additive and does not change the default GPT file-bundle behavior.
    """
    p, m = _coerce_provider_model(provider, model)
    profile = model_profile_for(p, m)
    return {
        "provider": p,
        "model": m,
        "model_profile_id": str(profile.get("id") or ""),
        "output_transport": _profiles_output_transport(profile),
        "transport_contract": _profiles_transport_contract(profile),
    }


# ---- Thin provider chat wrappers (test-friendly stubs) ----


def chat(messages: List[dict], model: str, provider: str | None = None) -> str:
    """
    Minimal provider router used by run_task wrappers and tests.
    In production, run_task carries the full OpenAI/Anthropic client logic.
    """
    p = (provider or default_provider()).strip().lower()
    if p == "openai":
        return chat_openai(messages, model)
    if p == "anthropic":
        return chat_anthropic(messages, model)
    raise RuntimeError(f"Unsupported provider: {p or 'unknown'}")


def chat_openai(messages: List[dict], model: str) -> str:
    """
    Placeholder OpenAI chat stub.
    The real OpenAI integration lives in agents.run_task; tests patch this module's symbols.
    """
    # Deterministic, side-effect-free default.
    _ = (_join_system_messages(messages), _messages_to_openai_responses_input(messages), model)
    # Return empty output; tests typically monkeypatch `chat` directly.
    return ""


def chat_anthropic(messages: List[dict], model: str) -> str:
    """
    Placeholder Anthropic chat stub.
    The real Anthropic integration lives in agents.run_task; tests patch this module's symbols.
    """
    _ = (_join_system_messages(messages), _non_system_messages(messages), model)
    return ""


__all__ = [
    # existing exports
    "default_provider",
    "default_model_for_provider",
    "default_api_mode_for_provider",
    "NormalizedLLMResponse",
    # new explicit transport/profile exports
    "model_profile_for",
    "output_transport_for_model",
    "transport_contract_for_model",
    "declared_transport_contract",
    # public transport/contract constants
    "TRANSPORT_FILE_BUNDLE",
    "TRANSPORT_PATCH",
    "CONTRACT_STRICT_FILE_BUNDLE",
    "CONTRACT_PATCH_APPLY_MODE",
    # chat stubs exposed for test monkeypatch and run_task wrapper delegation
    "chat",
    "chat_openai",
    "chat_anthropic",
]
