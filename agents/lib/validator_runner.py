from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Iterable, Protocol

from agents.lib import check_runner
from builder.orchestrator.project_config import ProjectConfig


@dataclass(frozen=True)
class ValidatorSpec:
    name: str
    command: str
    enabled: bool = True
    required: bool = True


@dataclass(frozen=True)
class ValidatorExecutionResult:
    name: str
    ok: bool
    output: str
    required: bool = True


class ValidatorRunnerProtocol(Protocol):
    def __call__(self, command: str, **kwargs: Any) -> subprocess.CompletedProcess[str]: ...


_LEGACY_COMMAND_SET = {"ruff check .", "pytest -q"}


def _normalize_spec(raw: Any) -> ValidatorSpec | None:
    if isinstance(raw, ValidatorSpec):
        return raw if raw.enabled else None
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name", "") or "").strip()
    command = str(raw.get("command", "") or "").strip()
    if not name or not command:
        return None
    enabled = bool(raw.get("enabled", True))
    required = bool(raw.get("required", True))
    if not enabled:
        return None
    return ValidatorSpec(name=name, command=command, enabled=enabled, required=required)


def normalize_validator_specs(raw_specs: Iterable[Any]) -> list[ValidatorSpec]:
    specs: list[ValidatorSpec] = []
    for raw in raw_specs:
        spec = _normalize_spec(raw)
        if spec is not None:
            specs.append(spec)
    return specs


def select_validators(config: ProjectConfig | None = None) -> list[ValidatorSpec]:
    if config is None or not getattr(config, "validators", None):
        return []
    raw = config.validators
    if isinstance(raw, list):
        return normalize_validator_specs(raw)
    return []


def _uses_legacy_builtin_suite(validators: list[ValidatorSpec]) -> bool:
    commands = {spec.command.strip() for spec in validators}
    return commands == _LEGACY_COMMAND_SET


def run_validator(spec: ValidatorSpec, *, runner: ValidatorRunnerProtocol | None = None) -> tuple[bool, str]:
    runner = runner or subprocess.run
    cp = runner(spec.command, shell=True, text=True, capture_output=True, check=False)
    stdout = (cp.stdout or "").strip()
    stderr = (cp.stderr or "").strip()
    ok = cp.returncode == 0
    header = f"[{spec.name}] {'ok' if ok else 'failed'}"
    detail = stderr or stdout
    return ok, f"{header}\n{detail}".strip()


def run_validators(validators: Iterable[ValidatorSpec]) -> dict[str, Any]:
    results: list[ValidatorExecutionResult] = []
    outputs: list[str] = []
    overall_ok = True
    for spec in validators:
        ok, output = run_validator(spec)
        results.append(ValidatorExecutionResult(name=spec.name, ok=ok, output=output, required=spec.required))
        outputs.append(output)
        if not ok and spec.required:
            overall_ok = False
    return {
        "ok": overall_ok,
        "output": "\n\n".join(outputs).strip(),
        "results": results,
    }


def _coerce_check_runner_result(result: dict[str, Any] | tuple[bool, str]) -> tuple[bool, str]:
    if isinstance(result, tuple) and len(result) == 2:
        return bool(result[0]), str(result[1])
    if isinstance(result, dict):
        lint_ok = bool(result.get("lint_ok", False))
        test_ok = bool(result.get("test_ok", False))
        output_text = str(result.get("output_text", "") or "")
        return lint_ok and test_ok, output_text.strip()
    raise TypeError(f"Unsupported run_checks() result shape: {type(result).__name__}")


def run_checks(config: ProjectConfig | None = None) -> tuple[bool, str]:
    validators = select_validators(config)
    if config is None or not validators or _uses_legacy_builtin_suite(validators):
        return _coerce_check_runner_result(check_runner.run_checks())

    executed = run_validators(validators)
    return bool(executed["ok"]), str(executed["output"])
