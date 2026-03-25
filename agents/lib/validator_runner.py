from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from agents.lib import check_runner
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

    return ValidatorSpec(
        name=name,
        command=command,
        enabled=bool(raw.get("enabled", True)),
        required=bool(raw.get("required", True)),
    )


def normalize_validator_specs(raw_specs: Iterable[Any] | None) -> tuple[ValidatorSpec, ...]:
    specs: list[ValidatorSpec] = []
    for raw in raw_specs or ():
        spec = _normalize_spec(raw)
        if spec is not None and spec.enabled:
            specs.append(spec)
    return tuple(specs)


def _resolve_config(config: ProjectConfig | str | Path | None) -> ProjectConfig | None:
    if config is None:
        return None
    if isinstance(config, ProjectConfig):
        return config
    return load_project_config(config)


def select_validators(config: ProjectConfig | str | Path | None = None) -> tuple[ValidatorSpec, ...]:
    resolved = _resolve_config(config)
    if resolved is None:
        return ()
    return normalize_validator_specs(resolved.validators)


def _coerce_check_runner_result(result: Any) -> tuple[bool, str]:
    if isinstance(result, tuple) and len(result) == 2:
        ok, output = result
        return bool(ok), str(output)

    lint_ok = bool(result.get("lint_ok", False))
    test_ok = bool(result.get("test_ok", False))
    output = str(result.get("output_text", "") or "")
    return lint_ok and test_ok, output


def _uses_legacy_builtin_suite(validators: tuple[ValidatorSpec, ...]) -> bool:
    commands = tuple(spec.command.strip() for spec in validators)
    return commands == _LEGACY_BUILTIN_COMMANDS and all(spec.required for spec in validators)


def run_validator(
    spec: ValidatorSpec,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str]:
    runner = runner or subprocess.run
    cp = runner(spec.command, shell=True, text=True, capture_output=True, check=False)

    output_parts = [part.strip() for part in (cp.stdout or "", cp.stderr or "") if part.strip()]
    ok = cp.returncode == 0
    header = f"[{spec.name}] {'ok' if ok else 'failed'}"
    output = "\n".join(output_parts).strip()
    if output:
        return ok, f"{header}\n{output}".strip()
    return ok, header


def _run_plugin_validators(
    validators: tuple[ValidatorSpec, ...],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str]:
    outputs: list[str] = []
    all_ok = True

    for spec in validators:
        ok, output = run_validator(spec, runner=runner)
        outputs.append(output)
        if spec.required and not ok:
            all_ok = False
            break

    return all_ok, "\n\n".join(outputs).strip()


def run_checks(
    config: ProjectConfig | str | Path | None = None,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str]:
    resolved = _resolve_config(config)
    validators = normalize_validator_specs(resolved.validators if resolved is not None else None)

    if resolved is None or not validators or _uses_legacy_builtin_suite(validators):
        return _coerce_check_runner_result(check_runner.run_checks())

    return _run_plugin_validators(validators, runner=runner)
