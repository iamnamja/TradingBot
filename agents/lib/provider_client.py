from __future__ import annotations

import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, List


_MODEL_VALIDATION_CACHE: Dict[str, set[str]] = {"openai": set(), "anthropic": set()}


class ProviderRequestTimeoutError(RuntimeError):
    pass


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


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
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


def _backoff_delay_seconds(attempt: int, retry_after: float | None = None, *, base: float = 1.0, cap: float = 30.0) -> float:
    if retry_after is not None and retry_after > 0:
        return min(cap, retry_after)
    delay = min(cap, base * (2 ** max(0, attempt - 1)))
    jitter = random.uniform(0.0, min(1.0, delay / 2 if delay > 0 else 0.5))
    return delay + jitter


def _status_code_from_exception(exc: Exception) -> int | None:
    code = getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        return status
    return None


def _provider_timeout_seconds(provider: str) -> float:
    provider = (provider or "").strip().lower()
    specific_name = ""
    if provider == "openai":
        specific_name = "TRADINGBOT_OPENAI_REQUEST_TIMEOUT_SECONDS"
    elif provider == "anthropic":
        specific_name = "TRADINGBOT_ANTHROPIC_REQUEST_TIMEOUT_SECONDS"
    if specific_name:
        specific = _float_env(specific_name, 0.0)
        if specific > 0:
            return specific
    return _float_env("TRADINGBOT_AGENT_PROVIDER_TIMEOUT_SECONDS", 120.0)


def _provider_heartbeat_seconds(provider: str) -> float:
    provider = (provider or "").strip().lower()
    specific_name = ""
    if provider == "openai":
        specific_name = "TRADINGBOT_OPENAI_REQUEST_HEARTBEAT_SECONDS"
    elif provider == "anthropic":
        specific_name = "TRADINGBOT_ANTHROPIC_REQUEST_HEARTBEAT_SECONDS"
    if specific_name:
        specific = _float_env(specific_name, 0.0)
        if specific > 0:
            return specific
    return _float_env("TRADINGBOT_AGENT_PROVIDER_HEARTBEAT_SECONDS", 15.0)


def _wait_for_provider_response(label: str, fn: Any, *, timeout_seconds: float, heartbeat_seconds: float) -> Any:
    start = time.monotonic()
    wait_seconds = heartbeat_seconds if heartbeat_seconds > 0 else 15.0
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn)
    print(f"→ Waiting for {label}", flush=True)
    try:
        while True:
            remaining: float | None = None
            if timeout_seconds > 0:
                elapsed = time.monotonic() - start
                remaining = timeout_seconds - elapsed
                if remaining <= 0:
                    future.cancel()
                    raise ProviderRequestTimeoutError(f"{label} timed out after {int(round(timeout_seconds))}s")
            wait_for = wait_seconds if remaining is None else min(wait_seconds, remaining)
            try:
                result = future.result(timeout=wait_for)
                elapsed = time.monotonic() - start
                print(f"✔ {label} returned in {int(round(elapsed))}s", flush=True)
                return result
            except FuturesTimeoutError:
                elapsed = time.monotonic() - start
                print(f"⏳ Still waiting for {label}... {int(round(elapsed))}s elapsed", flush=True)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _is_retryable_openai_error(exc: Exception) -> bool:
    if isinstance(exc, ProviderRequestTimeoutError):
        return False
    name = exc.__class__.__name__
    if name in {"RateLimitError", "APITimeoutError", "APIConnectionError", "InternalServerError"}:
        return True
    status = _status_code_from_exception(exc)
    if status in {408, 409, 429, 500, 502, 503, 504}:
        return True
    text = str(exc).lower()
    return "rate limit" in text or "timed out" in text or "temporarily unavailable" in text


def _is_retryable_anthropic_error(exc: Exception) -> bool:
    if isinstance(exc, ProviderRequestTimeoutError):
        return False
    name = exc.__class__.__name__.lower()
    if "timeout" in name or "connection" in name or "rate" in name:
        return True
    status = _status_code_from_exception(exc)
    if status in {408, 409, 429, 500, 502, 503, 504}:
        return True
    text = str(exc).lower()
    return "rate limit" in text or "timed out" in text or "temporarily unavailable" in text


def _extract_openai_response_text(resp: Any) -> str:
    output_text = getattr(resp, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    outputs = getattr(resp, "output", None)
    collected: List[str] = []
    if outputs:
        for item in outputs:
            item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
            if item_type == "message":
                content_list = getattr(item, "content", None) or (item.get("content") if isinstance(item, dict) else None) or []
                for block in content_list:
                    block_type = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
                    if block_type in {"output_text", "text"}:
                        text_val = getattr(block, "text", None) or (block.get("text") if isinstance(block, dict) else None)
                        if isinstance(text_val, str) and text_val:
                            collected.append(text_val)
            elif item_type in {"output_text", "text"}:
                text_val = getattr(item, "text", None) or (item.get("text") if isinstance(item, dict) else None)
                if isinstance(text_val, str) and text_val:
                    collected.append(text_val)
    return "\n".join(part.strip() for part in collected if part and part.strip()).strip()


def _normalize_openai_response(resp: Any) -> NormalizedLLMResponse:
    usage = getattr(resp, "usage", None)
    return NormalizedLLMResponse(
        text=_extract_openai_response_text(resp),
        stop_reason=getattr(resp, "status", None),
        usage_input_tokens=getattr(usage, "input_tokens", None) if usage is not None else None,
        usage_output_tokens=getattr(usage, "output_tokens", None) if usage is not None else None,
        request_id=getattr(resp, "id", None),
        raw_provider_response=resp,
    )


def _normalize_anthropic_response(resp: Any) -> NormalizedLLMResponse:
    parts: List[str] = []
    for block in getattr(resp, "content", []) or []:
        text_val = getattr(block, "text", None)
        if isinstance(text_val, str) and text_val:
            parts.append(text_val)
    usage = getattr(resp, "usage", None)
    return NormalizedLLMResponse(
        text="\n".join(part.strip() for part in parts if part and part.strip()).strip(),
        stop_reason=getattr(resp, "stop_reason", None),
        usage_input_tokens=getattr(usage, "input_tokens", None) if usage is not None else None,
        usage_output_tokens=getattr(usage, "output_tokens", None) if usage is not None else None,
        request_id=getattr(resp, "id", None),
        raw_provider_response=resp,
    )


def _should_skip_openai_model_validation() -> bool:
    if not _bool_env("TRADINGBOT_AGENT_VALIDATE_MODEL", False):
        return True
    if _bool_env("TRADINGBOT_AGENT_VALIDATE_MODEL_STRICT", False):
        return False
    # The OpenAI Models API preflight has proven brittle on Windows shells because
    # the SDK may trigger local platform/WMI inspection before generation starts.
    # Keep validation best-effort by default and allow strict mode to opt back in.
    return os.name == "nt"


def _maybe_validate_openai_model(client: Any, model: str) -> None:
    if _should_skip_openai_model_validation():
        return
    if model in _MODEL_VALIDATION_CACHE["openai"]:
        return
    strict = _bool_env("TRADINGBOT_AGENT_VALIDATE_MODEL_STRICT", False)
    try:
        client.models.retrieve(model)
    except Exception as exc:
        status = _status_code_from_exception(exc)
        if strict or status in {400, 401, 403, 404}:
            raise RuntimeError(
                f"OpenAI model `{model}` could not be retrieved via the Models API. Check the model ID and project access. Original error: {exc}"
            ) from exc
        return
    _MODEL_VALIDATION_CACHE["openai"].add(model)


def _maybe_validate_anthropic_model(client: Any, model: str) -> None:
    if not _bool_env("TRADINGBOT_AGENT_VALIDATE_MODEL", False):
        return
    if model in _MODEL_VALIDATION_CACHE["anthropic"]:
        return
    models_api = getattr(client, "models", None)
    if models_api is None:
        return
    getter = getattr(models_api, "get", None) or getattr(models_api, "retrieve", None)
    if callable(getter):
        try:
            getter(model)
        except TypeError:
            getter(model_id=model)
        except Exception:
            return
        _MODEL_VALIDATION_CACHE["anthropic"].add(model)


def _openai_generate_via_responses(client: Any, messages: List[dict], model: str) -> NormalizedLLMResponse:
    request: Dict[str, Any] = {
        "model": model,
        "instructions": _join_system_messages(messages),
        "input": _messages_to_openai_responses_input(messages),
    }
    max_output_tokens = _int_env("TRADINGBOT_OPENAI_MAX_OUTPUT_TOKENS", 20000)
    if max_output_tokens > 0:
        request["max_output_tokens"] = max_output_tokens
    effort = os.getenv("TRADINGBOT_OPENAI_REASONING_EFFORT", "").strip().lower()
    if effort in {"minimal", "low", "medium", "high"}:
        request["reasoning"] = {"effort": effort}
    resp = client.responses.create(**request)
    return _normalize_openai_response(resp)


def _openai_generate_via_chat_completions(client: Any, messages: List[dict], model: str) -> NormalizedLLMResponse:
    resp = client.chat.completions.create(model=model, messages=messages)
    content = resp.choices[0].message.content
    usage = getattr(resp, "usage", None)
    return NormalizedLLMResponse(
        text=content.strip() if isinstance(content, str) else "",
        stop_reason=getattr(resp.choices[0], "finish_reason", None),
        usage_input_tokens=getattr(usage, "prompt_tokens", None) if usage is not None else None,
        usage_output_tokens=getattr(usage, "completion_tokens", None) if usage is not None else None,
        request_id=getattr(resp, "id", None),
        raw_provider_response=resp,
    )


def _make_openai_client(timeout_seconds: float) -> Any:
    from openai import OpenAI

    if timeout_seconds > 0:
        try:
            return OpenAI(timeout=timeout_seconds)
        except TypeError:
            pass
    return OpenAI()


def _make_anthropic_client(timeout_seconds: float) -> Any:
    from anthropic import Anthropic

    if timeout_seconds > 0:
        try:
            return Anthropic(timeout=timeout_seconds)
        except TypeError:
            pass
    return Anthropic()


def chat_openai(messages: List[dict], model: str) -> str:
    timeout_seconds = _provider_timeout_seconds("openai")
    heartbeat_seconds = _provider_heartbeat_seconds("openai")
    client = _make_openai_client(timeout_seconds)
    _maybe_validate_openai_model(client, model)
    api_mode = default_api_mode_for_provider("openai")
    retries = max(1, _int_env("TRADINGBOT_AGENT_PROVIDER_RETRIES", 3))
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            label = f"OpenAI {api_mode or 'responses'} request (attempt {attempt}/{retries}, model {model})"
            if api_mode == "chat_completions":
                result = _wait_for_provider_response(
                    label,
                    lambda: _openai_generate_via_chat_completions(client, messages, model),
                    timeout_seconds=timeout_seconds,
                    heartbeat_seconds=heartbeat_seconds,
                )
            else:
                result = _wait_for_provider_response(
                    label,
                    lambda: _openai_generate_via_responses(client, messages, model),
                    timeout_seconds=timeout_seconds,
                    heartbeat_seconds=heartbeat_seconds,
                )
            return (result.text or "").strip()
        except Exception as exc:
            last_exc = exc
            if attempt >= retries or not _is_retryable_openai_error(exc):
                raise
            delay = _backoff_delay_seconds(attempt, _extract_retry_after_seconds(exc))
            print(f"↻ Retrying OpenAI request after {delay:.1f}s due to: {exc}", flush=True)
            time.sleep(delay)
    if last_exc is not None:
        raise last_exc
    return ""


def chat_anthropic(messages: List[dict], model: str) -> str:
    timeout_seconds = _provider_timeout_seconds("anthropic")
    heartbeat_seconds = _provider_heartbeat_seconds("anthropic")
    client = _make_anthropic_client(timeout_seconds)
    _maybe_validate_anthropic_model(client, model)
    retries = max(1, _int_env("TRADINGBOT_AGENT_PROVIDER_RETRIES", 3))
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            system_text = _join_system_messages(messages)
            non_system = _non_system_messages(messages)
            request: Dict[str, Any] = {
                "model": model,
                "max_tokens": max(1, _int_env("TRADINGBOT_ANTHROPIC_MAX_TOKENS", 20000)),
                "messages": [{"role": m["role"] if m["role"] in {"user", "assistant"} else "user", "content": m["content"]} for m in non_system],
            }
            if system_text:
                request["system"] = system_text
            label = f"Anthropic messages request (attempt {attempt}/{retries}, model {model})"
            resp = _wait_for_provider_response(
                label,
                lambda: client.messages.create(**request),
                timeout_seconds=timeout_seconds,
                heartbeat_seconds=heartbeat_seconds,
            )
            result = _normalize_anthropic_response(resp)
            return (result.text or "").strip()
        except Exception as exc:
            last_exc = exc
            if attempt >= retries or not _is_retryable_anthropic_error(exc):
                raise
            delay = _backoff_delay_seconds(attempt, _extract_retry_after_seconds(exc))
            print(f"↻ Retrying Anthropic request after {delay:.1f}s due to: {exc}", flush=True)
            time.sleep(delay)
    if last_exc is not None:
        raise last_exc
    return ""


def chat(messages: List[dict], model: str, provider: str | None = None) -> str:
    selected = (provider or default_provider()).strip().lower()
    if selected == "openai":
        return chat_openai(messages, model)
    if selected == "anthropic":
        return chat_anthropic(messages, model)
    raise ValueError(f"Unsupported provider: {selected}")
