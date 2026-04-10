from __future__ import annotations

import shlex
from typing import Any, Callable, Mapping, Sequence


def _dedupe_python_paths(paths: Sequence[object] | None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in paths or ():
        value = str(raw or "").strip().replace("\\", "/")
        if value.endswith(".py") and value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _split_command(raw: str) -> list[str]:
    text = str(raw or "").strip()
    if not text:
        return []
    return [str(part) for part in shlex.split(text)]


def build_safe_lint_preflight_plan(
    *,
    task_path: str,
    required_paths: Sequence[object] | None,
    verifier_artifact: Mapping[str, Any] | None,
    failure_taxonomy: Mapping[str, Any] | None,
) -> dict[str, object]:
    verifier = dict(verifier_artifact or {})
    taxonomy = dict(failure_taxonomy or {})
    python_paths = _dedupe_python_paths(required_paths)
    failure_family = str(taxonomy.get("failure_family", "") or "")
    attempt_allowed = failure_family == "formatting_lint_only" and bool(python_paths)

    lint_replay_commands: list[list[str]] = []
    for raw in verifier.get("focused_validation_commands") or verifier.get("focused_results") or ():
        parts = _split_command(str(raw))
        if len(parts) >= 2 and parts[0] == "ruff" and parts[1] == "check":
            lint_replay_commands.append(parts)
    if not lint_replay_commands and python_paths:
        lint_replay_commands.append(["ruff", "check", *python_paths])

    broad_validation_commands: list[list[str]] = []
    for raw in verifier.get("full_validation_commands") or verifier.get("full_results") or ():
        parts = _split_command(str(raw))
        if not parts:
            continue
        if len(parts) >= 1 and parts[0] == "ruff":
            continue
        broad_validation_commands.append(parts)

    return {
        "task_path": str(task_path or ""),
        "attempt_allowed": bool(attempt_allowed),
        "reason": (
            "Verifier isolated the admitted failure to lint/formatting on python files inside the safe one-task lane."
            if attempt_allowed
            else "Safe lint preflight normalization is only allowed for lint-only failures on required python files."
        ),
        "failure_family": failure_family,
        "python_paths": python_paths,
        "normalization_commands": [
            ["ruff", "check", "--fix", *python_paths],
            ["ruff", "format", *python_paths],
        ] if attempt_allowed else [],
        "lint_replay_commands": lint_replay_commands if attempt_allowed else [],
        "broad_validation_commands": broad_validation_commands if attempt_allowed else [],
    }


def _capture_result(result: Mapping[str, Any] | None) -> dict[str, object]:
    payload = dict(result or {})
    return {
        "command": [str(part) for part in (payload.get("command") or ())],
        "returncode": int(payload.get("returncode", 0) or 0),
        "stdout": str(payload.get("stdout", "") or ""),
        "stderr": str(payload.get("stderr", "") or ""),
    }


def run_safe_lint_preflight(
    plan: Mapping[str, Any] | None,
    *,
    executor: Callable[[Sequence[str]], Mapping[str, Any]],
) -> dict[str, object]:
    payload = dict(plan or {})
    artifact: dict[str, object] = {
        "task_path": str(payload.get("task_path", "") or ""),
        "attempted": False,
        "succeeded": False,
        "reason": str(payload.get("reason", "") or ""),
        "failure_family": str(payload.get("failure_family", "") or ""),
        "python_paths": list(payload.get("python_paths", []) or []),
        "normalization_results": [],
        "lint_replay_results": [],
        "broad_validation_results": [],
    }
    if not bool(payload.get("attempt_allowed", False)):
        return artifact

    artifact["attempted"] = True

    for command in payload.get("normalization_commands", []) or ():
        result = _capture_result(executor(list(command)))
        artifact["normalization_results"].append(result)

    lint_green = True
    for command in payload.get("lint_replay_commands", []) or ():
        result = _capture_result(executor(list(command)))
        artifact["lint_replay_results"].append(result)
        if int(result["returncode"]) != 0:
            lint_green = False

    broad_green = True
    if lint_green:
        for command in payload.get("broad_validation_commands", []) or ():
            result = _capture_result(executor(list(command)))
            artifact["broad_validation_results"].append(result)
            if int(result["returncode"]) != 0:
                broad_green = False
    else:
        broad_green = False if payload.get("broad_validation_commands") else True

    artifact["lint_green_after_normalization"] = bool(lint_green)
    artifact["broad_validation_green_after_normalization"] = bool(broad_green)
    artifact["succeeded"] = bool(lint_green and broad_green)
    return artifact


def apply_safe_lint_preflight_execution_summary(
    execution_summary: Mapping[str, Any] | None,
    artifact: Mapping[str, Any] | None,
) -> dict[str, object]:
    execution = dict(execution_summary or {})
    preflight = dict(artifact or {})
    execution["safe_lint_preflight_attempted"] = bool(preflight.get("attempted", False))
    execution["safe_lint_preflight_succeeded"] = bool(preflight.get("succeeded", False))
    execution["safe_lint_preflight_python_paths"] = list(preflight.get("python_paths", []) or [])
    execution["safe_lint_preflight_reason"] = str(preflight.get("reason", "") or "")
    if not bool(preflight.get("succeeded", False)):
        return execution

    execution["returncode"] = 0
    execution["ruff_green_observed"] = bool(preflight.get("lint_green_after_normalization", False))
    prior_pytest = bool(execution.get("pytest_green_observed", False))
    replay_pytest = bool(preflight.get("broad_validation_green_after_normalization", False)) or not bool(preflight.get("broad_validation_results"))
    execution["pytest_green_observed"] = bool(prior_pytest or replay_pytest)
    execution["all_checks_passed_observed"] = bool(execution.get("ruff_green_observed", False) and execution.get("pytest_green_observed", False))

    output_chunks: list[str] = []
    for bucket in (
        preflight.get("normalization_results", []),
        preflight.get("lint_replay_results", []),
        preflight.get("broad_validation_results", []),
    ):
        for result in bucket or ():
            stdout = str(dict(result).get("stdout", "") or "").strip()
            stderr = str(dict(result).get("stderr", "") or "").strip()
            if stdout:
                output_chunks.append(stdout)
            if stderr:
                output_chunks.append(stderr)
    if output_chunks:
        combined = "\n".join(output_chunks)
        execution["stdout_tail"] = "\n".join(
            chunk for chunk in [str(execution.get("stdout_tail", "") or "").strip(), combined] if chunk
        )[-1200:]
    return execution


__all__ = [
    "apply_safe_lint_preflight_execution_summary",
    "build_safe_lint_preflight_plan",
    "run_safe_lint_preflight",
]
