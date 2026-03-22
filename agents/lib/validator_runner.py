
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ValidatorSpec:
    name: str
    command: str | list[str]
    enabled: bool = True
    required: bool = True


ValidationResult = tuple[bool, str]
DefaultRunner = Callable[[], Any]


def _coerce_validator(item: ValidatorSpec | dict[str, Any]) -> ValidatorSpec:
    if isinstance(item, ValidatorSpec):
        return item
    if not isinstance(item, dict):
        raise TypeError(f"Unsupported validator definition: {type(item).__name__}")
    command = item.get("command")
    if not isinstance(command, (str, list, tuple)):
        raise TypeError("Validator command must be a string or sequence of strings")
    if isinstance(command, tuple):
        command = list(command)
    return ValidatorSpec(
        name=str(item.get("name", "validator") or "validator"),
        command=command,
        enabled=bool(item.get("enabled", True)),
        required=bool(item.get("required", True)),
    )


def _raw_validators(config: Any) -> list[ValidatorSpec]:
    if config is None:
        return []
    raw = getattr(config, "validators", None)
    if raw is None and isinstance(config, dict):
        raw = config.get("validators")
    if raw is None:
        return []
    return [_coerce_validator(item) for item in raw]


def select_validators(config: Any) -> list[ValidatorSpec]:
    return [validator for validator in _raw_validators(config) if validator.enabled]


def _normalize_result(result: Any) -> ValidationResult:
    if (
        isinstance(result, tuple)
        and len(result) == 2
        and isinstance(result[0], bool)
        and isinstance(result[1], str)
    ):
        return result
    if isinstance(result, dict):
        lint_ok = bool(result.get("lint_ok", False))
        test_ok = bool(result.get("test_ok", False))
        output_text = str(result.get("output_text", "") or "")
        return (lint_ok and test_ok), output_text.strip()
    raise TypeError(f"Unsupported validator result shape: {type(result).__name__}")


def _default_validation_runner() -> ValidationResult:
    from agents.lib.check_runner import run_checks as _run_default_checks

    return _normalize_result(_run_default_checks())


def _run_command(command: str | list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=isinstance(command, str),
    )


def run_checks(config: Any = None, default_runner: DefaultRunner | None = None) -> ValidationResult:
    validators = select_validators(config)
    if not validators:
        runner = default_runner or _default_validation_runner
        return _normalize_result(runner())

    all_ok = True
    lines: list[str] = []
    for validator in validators:
        result = _run_command(validator.command)
        passed = result.returncode == 0
        if passed:
            lines.append(f"[{validator.name}] ok")
            rendered = str(result.stdout or "").strip()
            if rendered:
                lines.append(rendered)
            continue

        if validator.required:
            all_ok = False
        lines.append(f"=== {validator.name} ===")
        rendered = str(result.stdout or "").strip()
        if rendered:
            lines.append(rendered)
        lines.append("(required validator failed)" if validator.required else "(non-required validator failed)")

    return all_ok, "\n".join(line for line in lines if line).strip()
