from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from agents.lib import check_runner
from builder.orchestrator.project_adapter import ProjectAdapter
from builder.orchestrator.project_config import ProjectConfig, load_project_config


@dataclass(frozen=True)
class ValidatorSpec:
    name: str
    command: str
    enabled: bool = True
    required: bool = True


_LEGACY_BUILTIN_COMMANDS: tuple[str, ...] = (
    "ruff check .",
    "pytest -q",
)


def _normalize_spec(raw: Any) -> ValidatorSpec | None:
    if isinstance(raw, ValidatorSpec):
        return raw
    if not isinstance(raw, dict):
        return None

    name = str(raw.get("name", "") or "").strip()
    command = str(raw.get("command", "") or "").strip()
    if not name or not command:
        return None

    enabled = bool(raw.get("enabled", True))
    required = bool(raw.get("required", True))
    return ValidatorSpec(name=name, command=command, enabled=enabled, required=required)


def normalize_validator_specs(raw_specs: Iterable[Any]) -> list[ValidatorSpec]:
    specs: list[ValidatorSpec] = []
    for raw in raw_specs:
        spec = _normalize_spec(raw)
        if spec is None or not spec.enabled:
            continue
        specs.append(spec)
    return specs


def select_validators(config: ProjectConfig | None = None) -> list[ValidatorSpec]:
    cfg = config or load_project_config()
    adapter = ProjectAdapter(cfg)
    behavior = adapter.translate_to_orchestrator_behavior()

    raw_validators = behavior.get("validators")
    if isinstance(raw_validators, list):
        return normalize_validator_specs(raw_validators)
    return []


def _uses_legacy_builtin_suite(validators: list[ValidatorSpec]) -> bool:
    commands = tuple(spec.command.strip() for spec in validators)
    if commands != _LEGACY_BUILTIN_COMMANDS:
        return False
    return all(spec.required for spec in validators)


def run_validator(
    spec: ValidatorSpec,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str]:
    runner = runner or subprocess.run
    cp = runner(spec.command, shell=True, text=True, capture_output=True, check=False)
    stdout = (cp.stdout or "").strip()
    stderr = (cp.stderr or "").strip()

    output_parts: list[str] = []
    if stdout:
        output_parts.append(stdout)
    if stderr:
        output_parts.append(stderr)

    ok = cp.returncode == 0
    header = f"[{spec.name}] {'ok' if ok else 'failed'}"
    output = "\n".join(output_parts).strip()
    return ok, f"{header}\n{output}".strip()


def _coerce_check_runner_result(result: dict[str, Any] | tuple[bool, str]) -> tuple[bool, str]:
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
    raise TypeError(f"Unsupported run_checks() result shape: {type(result).__name__}")


def run_checks(config: ProjectConfig | None = None) -> tuple[bool, str]:
    cfg = config or load_project_config()
    validators = select_validators(cfg)

    if not validators or _uses_legacy_builtin_suite(validators):
        return _coerce_check_runner_result(check_runner.run_checks())

    all_ok = True
    outputs: list[str] = []
    for spec in validators:
        ok, text = run_validator(spec)
        outputs.append(text)
        if not ok and spec.required:
            all_ok = False

    return all_ok, "\n\n".join(outputs).strip()