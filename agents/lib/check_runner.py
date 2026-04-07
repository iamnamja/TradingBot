from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Mapping, Tuple


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def capture_result(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


_DEFAULT_CAPTURE_RESULT = capture_result


def _capture_result_overridden() -> bool:
    return capture_result is not _DEFAULT_CAPTURE_RESULT


def _coerce_completed_output(result: object) -> str:
    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    if stderr and stderr not in stdout:
        return f"{stdout}{stderr}".strip()
    return str(stdout).strip()


_PYTEST_FAILED_NODE_RE = re.compile(r"^FAILED\s+([^\s]+)", re.MULTILINE)
_PYTEST_TEST_FILE_RE = re.compile(r"^(tests[\/][^\n:]+):(\d+):", re.MULTILINE)
_MODULE_NOT_FOUND_RE = re.compile(r"ModuleNotFoundError: No module named '([^']+)'")
_CANNOT_IMPORT_RE = re.compile(r"cannot import name '([^']+)' from '([^']+)'")
_PATH_TOKEN_RE = re.compile(r"(?:agents|builder|docs|src|tasks|tests)[\/][A-Za-z0-9_./-]+\.(?:py|md)")


def _coerce_string_list(value: object) -> list[str]:
    items = value if isinstance(value, (list, tuple)) else []
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in items:
        text = str(raw or "").strip()
        if text and text not in seen:
            normalized.append(text)
            seen.add(text)
    return normalized


def _bounded_output_excerpt(text: str, *, max_chars: int = 400) -> str:
    value = str(text or "").strip()
    if len(value) <= max_chars:
        return value
    suffix = "...[truncated]"
    return f"{value[: max(0, max_chars - len(suffix))]}{suffix}"


def _normalize_path(path: str) -> str:
    return str(path or "").strip().replace("\\", "/")


def _module_name_to_path(module_name: str) -> str:
    module = str(module_name or "").strip().replace(".", "/")
    if not module:
        return ""
    if module.endswith("/__init__"):
        return f"{module}.py"
    return f"{module}.py"


def _collect_failed_test_nodes(output_text: str) -> list[str]:
    nodes: list[str] = []
    seen: set[str] = set()
    for match in _PYTEST_FAILED_NODE_RE.finditer(output_text):
        node = str(match.group(1) or "").strip()
        if node and node not in seen:
            nodes.append(node)
            seen.add(node)
    return nodes


def _collect_failed_test_files(output_text: str, failed_nodes: list[str]) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for node in failed_nodes:
        file_token = _normalize_path(node.split("::", 1)[0])
        if file_token.startswith("tests/") and file_token not in seen:
            files.append(file_token)
            seen.add(file_token)
    for match in _PYTEST_TEST_FILE_RE.finditer(output_text):
        file_token = _normalize_path(str(match.group(1) or ""))
        if file_token and file_token not in seen:
            files.append(file_token)
            seen.add(file_token)
    return files


def _collect_likely_touched_files(output_text: str, *, fallback_files: list[str] | None = None) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()

    for raw in fallback_files or []:
        path = _normalize_path(raw)
        if path and path not in seen:
            files.append(path)
            seen.add(path)

    for match in _MODULE_NOT_FOUND_RE.finditer(output_text):
        path = _module_name_to_path(str(match.group(1) or ""))
        if path and path not in seen:
            files.append(path)
            seen.add(path)

    for match in _CANNOT_IMPORT_RE.finditer(output_text):
        path = _module_name_to_path(str(match.group(2) or ""))
        if path and path not in seen:
            files.append(path)
            seen.add(path)

    for raw in _PATH_TOKEN_RE.findall(output_text):
        path = _normalize_path(raw)
        if path and path not in seen:
            files.append(path)
            seen.add(path)

    return files


def _classify_failure_family(output_text: str, *, lint_ok: bool, test_ok: bool) -> str:
    text = str(output_text or "").lower()
    if not text and lint_ok and test_ok:
        return "pass"
    if any(token in text for token in ("modulenotfounderror", "importerror while importing test module", "cannot import name", "attributeerror")):
        return "import_contract"
    if any(token in text for token in ("keyerror", "unexpected result", "result shape", "missing truth field", "missing export", "decision mismatch")):
        return "result_shape"
    if any(token in text for token in ("docs/", "readme", "documentation claim", "proof claim", "status narrative")):
        return "docs_drift"
    if not lint_ok:
        return "lint_failure"
    return "execution_failure"


def _derive_focused_replay_commands(
    *,
    lint_ok: bool,
    test_ok: bool,
    failed_nodes: list[str],
    failed_files: list[str],
    likely_touched_files: list[str],
) -> list[str]:
    commands: list[str] = []
    seen: set[str] = set()

    if not lint_ok:
        lint_targets = [path for path in likely_touched_files if path.endswith(".py")][:3]
        lint_cmd = "ruff check ." if not lint_targets else f"ruff check {' '.join(lint_targets)}"
        commands.append(lint_cmd)
        seen.add(lint_cmd)

    if not test_ok:
        for node in failed_nodes[:2]:
            cmd = f"pytest -q {node}"
            if cmd not in seen:
                commands.append(cmd)
                seen.add(cmd)
        for path in failed_files[:2]:
            cmd = f"pytest -q {path}"
            if cmd not in seen:
                commands.append(cmd)
                seen.add(cmd)
        if not failed_nodes and not failed_files:
            cmd = "pytest -q"
            commands.append(cmd)
            seen.add(cmd)

    return commands[:4]


def _derive_broad_replay_commands(*, lint_ok: bool, test_ok: bool) -> list[str]:
    commands: list[str] = []
    if not lint_ok:
        commands.append("ruff check .")
    if not test_ok:
        commands.append("pytest -q")
    return commands


def build_tester_critique_bundle(
    payload: Mapping[str, object] | None = None,
    *,
    lint_ok: bool | None = None,
    test_ok: bool | None = None,
    output_text: str | None = None,
    focused_results: list[str] | tuple[str, ...] | None = None,
    full_results: list[str] | tuple[str, ...] | None = None,
    changed_files: list[str] | tuple[str, ...] | None = None,
    failure_category: str | None = None,
    failure_message: str | None = None,
) -> dict[str, object]:
    data = dict(payload or {})
    lint_status = bool(lint_ok if lint_ok is not None else data.get("lint_ok", True))
    test_status = bool(test_ok if test_ok is not None else data.get("test_ok", True))
    raw_output = str(
        output_text
        if output_text is not None
        else data.get("output_text")
        or data.get("validator_note")
        or data.get("failure_message")
        or failure_message
        or ""
    ).strip()
    failed_nodes = _coerce_string_list(data.get("failing_test_nodes")) or _collect_failed_test_nodes(raw_output)
    failed_files = _coerce_string_list(data.get("failing_test_files")) or _collect_failed_test_files(raw_output, failed_nodes)
    explicit_likely_touched = _coerce_string_list(data.get("likely_touched_files"))
    likely_touched = explicit_likely_touched or _collect_likely_touched_files(
        raw_output,
        fallback_files=_coerce_string_list(changed_files if changed_files is not None else data.get("changed_files")),
    )
    family = str(data.get("likely_failure_family") or "").strip() or _classify_failure_family(raw_output, lint_ok=lint_status, test_ok=test_status)
    focused_commands = _coerce_string_list(data.get("focused_replay_commands")) or _coerce_string_list(focused_results if focused_results is not None else data.get("focused_results"))
    if not focused_commands:
        focused_commands = _derive_focused_replay_commands(
            lint_ok=lint_status,
            test_ok=test_status,
            failed_nodes=failed_nodes,
            failed_files=failed_files,
            likely_touched_files=likely_touched,
        )
    broad_commands = _coerce_string_list(data.get("broad_replay_commands")) or _coerce_string_list(full_results if full_results is not None else data.get("full_results"))
    if not broad_commands:
        broad_commands = _derive_broad_replay_commands(lint_ok=lint_status, test_ok=test_status)

    if lint_status and test_status:
        critique_summary = "Validation passed locally; no focused replay is currently required."
    elif family == "import_contract":
        critique_summary = "Tester found likely import/contract drift; replay should start with the smallest failing file or node."
    elif family == "result_shape":
        critique_summary = "Tester found likely result-shape drift; replay should start with the smallest failing test node or file."
    elif family == "docs_drift":
        critique_summary = "Tester found likely docs/status drift; replay should start with the narrowest documentation proof surface."
    else:
        critique_summary = "Tester found broader execution failure; replay should start focused and only widen after the first bounded rerun."

    failure_clusters: list[dict[str, object]] = []
    if failed_files:
        failure_clusters.append({"cluster_type": "failing_test_files", "items": failed_files[:3], "count": len(failed_files)})
    if failed_nodes:
        failure_clusters.append({"cluster_type": "failing_test_nodes", "items": failed_nodes[:3], "count": len(failed_nodes)})
    if likely_touched:
        failure_clusters.append({"cluster_type": "likely_touched_files", "items": likely_touched[:3], "count": len(likely_touched)})

    return {
        "schema_version": 1,
        "lint_ok": lint_status,
        "test_ok": test_status,
        "all_checks_passed": bool(lint_status and test_status),
        "likely_failure_family": family,
        "failure_category": str(failure_category if failure_category is not None else data.get("failure_category") or "").strip(),
        "critique_summary": str(data.get("critique_summary") or critique_summary),
        "failing_test_nodes": failed_nodes[:5],
        "failing_test_files": failed_files[:5],
        "likely_touched_files": likely_touched[:5],
        "failure_clusters": failure_clusters,
        "focused_replay_commands": focused_commands[:4],
        "broad_replay_commands": broad_commands[:3],
        "raw_output_excerpt": _bounded_output_excerpt(raw_output),
    }


def build_ordinary_task_execution_plan(
    payload: Mapping[str, object] | None = None,
    *,
    task_context: Mapping[str, object] | None = None,
    changed_files: list[str] | tuple[str, ...] | None = None,
) -> dict[str, object]:
    data = dict(payload or {})
    context = dict(task_context or {})
    critique_payload = data.get("tester_critique_bundle") if isinstance(data.get("tester_critique_bundle"), Mapping) else data.get("critique_bundle")
    critique = build_tester_critique_bundle(
        critique_payload if isinstance(critique_payload, Mapping) else None,
        lint_ok=(data["lint_ok"] if "lint_ok" in data else None),
        test_ok=(data["test_ok"] if "test_ok" in data else None),
        output_text=str(data.get("output_text") or data.get("validator_note") or data.get("failure_message") or ""),
        focused_results=_coerce_string_list(data.get("focused_results")),
        full_results=_coerce_string_list(data.get("full_results")),
        changed_files=_coerce_string_list(changed_files if changed_files is not None else data.get("changed_files")),
        failure_category=str(data.get("failure_category") or ""),
        failure_message=str(data.get("failure_message") or ""),
    )
    admission_lane = str(context.get("task_admission_lane") or data.get("task_admission_lane") or "autonomous_ordinary")
    focused_commands = list(critique.get("focused_replay_commands") or [])
    broad_commands = list(critique.get("broad_replay_commands") or [])

    if admission_lane == "manual_only":
        validation_mode = "manual_only"
        should_run_broad_validation = False
        controller_review_required = True
        summary = "Ordinary task execution is not admitted for this task shape; keep controller/manual handling."
    elif critique.get("likely_failure_family") == "pass":
        validation_mode = "focused_then_broad" if broad_commands else "no_validation_required"
        should_run_broad_validation = bool(broad_commands)
        controller_review_required = True
        summary = "Tester evidence is green; broader validation may still run, but controller authority remains final."
    elif focused_commands:
        validation_mode = "focused_then_broad"
        should_run_broad_validation = True
        controller_review_required = True
        summary = "Tester should replay focused failures first, then widen to broader validation only if needed."
    elif broad_commands:
        validation_mode = "broad_only"
        should_run_broad_validation = True
        controller_review_required = True
        summary = "Tester has no focused replay target and should fall back to broad validation."
    else:
        validation_mode = "controller_review"
        should_run_broad_validation = False
        controller_review_required = True
        summary = "Tester evidence is incomplete; controller review is required before widening validation."

    return {
        "task_admission_lane": admission_lane,
        "ordinary_task_execution": admission_lane in {"autonomous_ordinary", "supervised_autonomous"},
        "validation_mode": validation_mode,
        "focused_replay_commands": focused_commands,
        "broad_replay_commands": broad_commands,
        "should_run_broad_validation": should_run_broad_validation,
        "controller_review_required": controller_review_required,
        "summary": summary,
        "likely_failure_family": str(critique.get("likely_failure_family") or ""),
    }


def summarize_tester_critique_bundle(payload: Mapping[str, object] | None = None, **overrides: object) -> dict[str, object]:
    bundle = build_tester_critique_bundle(payload, **overrides)
    return {
        "likely_failure_family": bundle["likely_failure_family"],
        "critique_summary": bundle["critique_summary"],
        "failing_test_files": list(bundle["failing_test_files"]),
        "likely_touched_files": list(bundle["likely_touched_files"]),
        "focused_replay_commands": list(bundle["focused_replay_commands"]),
        "broad_replay_commands": list(bundle["broad_replay_commands"]),
    }


def _run_command_with_heartbeat(
    exec_cmd: List[str],
    *,
    label: str,
    timeout_seconds: int,
    heartbeat_seconds: int,
) -> Tuple[bool, str, bool]:
    print(f"▶ Running {label}", flush=True)
    start = time.monotonic()
    proc = subprocess.Popen(
        exec_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    while True:
        elapsed = time.monotonic() - start
        remaining = max(0.0, float(timeout_seconds) - elapsed)
        if remaining <= 0:
            proc.kill()
            stdout, _ = proc.communicate()
            timeout_msg = f"\n\n[timeout] {label} exceeded {timeout_seconds}s and was terminated."
            return False, (stdout or "").strip() + timeout_msg, True

        try:
            stdout, _ = proc.communicate(timeout=min(float(heartbeat_seconds), remaining))
            break
        except subprocess.TimeoutExpired:
            print(f"⏳ Still running {label}... {int(time.monotonic() - start)}s elapsed", flush=True)

    output = (stdout or "").strip()
    ok = proc.returncode == 0
    duration = int(time.monotonic() - start)
    status = "ok" if ok else f"exit={proc.returncode}"
    print(f"✔ Finished {label} ({status}, {duration}s)", flush=True)
    return ok, output, False


def _nested_pytest_guard(exec_cmd: List[str], label: str) -> Tuple[bool, str, bool] | None:
    if os.getenv("TRADINGBOT_ALLOW_NESTED_PYTEST", "").strip().lower() in {"1", "true", "yes", "on"}:
        return None
    in_pytest = bool(os.getenv("PYTEST_CURRENT_TEST", "").strip())
    if not in_pytest:
        return None
    normalized = [part.strip().lower() for part in exec_cmd]
    if normalized[-2:] != ["pytest", "-q"] and normalized != ["pytest", "-q"]:
        return None
    message = (
        f"Nested repo-wide {label} invocation was blocked while already running under pytest. "
        "Monkeypatch the validator/check execution path or set TRADINGBOT_ALLOW_NESTED_PYTEST=1 if this is intentional."
    )
    print(f"✔ Skipped {label} (nested-pytest-guard, 0s)", flush=True)
    return False, message, False


def _run_check_command(
    display_cmd: List[str],
    *,
    exec_cmd: List[str],
    label: str,
    timeout_seconds: int,
    heartbeat_seconds: int,
) -> Tuple[bool, str, bool]:
    if _capture_result_overridden():
        print(f"▶ Running {label}", flush=True)
        result = capture_result(display_cmd)
        ok = getattr(result, "returncode", 1) == 0
        output = _coerce_completed_output(result)
        status = "ok" if ok else f"exit={getattr(result, 'returncode', 1)}"
        print(f"✔ Finished {label} ({status}, 0s)", flush=True)
        return ok, output, False

    nested_guard = _nested_pytest_guard(exec_cmd, label)
    if nested_guard is not None:
        return nested_guard

    return _run_command_with_heartbeat(
        exec_cmd,
        label=label,
        timeout_seconds=timeout_seconds,
        heartbeat_seconds=heartbeat_seconds,
    )


def run_checks() -> Dict[str, Any] | Tuple[bool, str]:
    heartbeat_seconds = max(5, _int_env("TRADINGBOT_CHECK_HEARTBEAT_SECONDS", 15))
    ruff_timeout_seconds = max(30, _int_env("TRADINGBOT_RUFF_TIMEOUT_SECONDS", 180))
    pytest_timeout_seconds = max(60, _int_env("TRADINGBOT_PYTEST_TIMEOUT_SECONDS", 600))

    lint_ok, lint_output, lint_timed_out = _run_check_command(
        ["ruff", "check", "."],
        exec_cmd=[sys.executable, "-m", "ruff", "check", "."],
        label="ruff check .",
        timeout_seconds=ruff_timeout_seconds,
        heartbeat_seconds=heartbeat_seconds,
    )
    test_ok, test_output, test_timed_out = _run_check_command(
        ["pytest", "-q"],
        exec_cmd=[sys.executable, "-m", "pytest", "-q"],
        label="pytest -q",
        timeout_seconds=pytest_timeout_seconds,
        heartbeat_seconds=heartbeat_seconds,
    )

    chunks: List[str] = []
    if not lint_ok:
        chunks.append("=== ruff check . ===")
        if lint_output:
            chunks.append(lint_output)
        if lint_timed_out:
            chunks.append(
                f"ruff timed out after {ruff_timeout_seconds}s. Increase TRADINGBOT_RUFF_TIMEOUT_SECONDS if this is expected."
            )
    if not test_ok:
        chunks.append("=== pytest -q ===")
        if test_output:
            chunks.append(test_output)
        if test_timed_out:
            chunks.append(
                f"pytest timed out after {pytest_timeout_seconds}s. Increase TRADINGBOT_PYTEST_TIMEOUT_SECONDS if this is expected."
            )

    output_text = "\n\n".join(chunk for chunk in chunks if chunk).strip()
    critique_bundle = build_tester_critique_bundle(
        {
            "lint_ok": lint_ok,
            "test_ok": test_ok,
            "output_text": output_text,
        }
    )
    return {
        "lint_ok": lint_ok,
        "test_ok": test_ok,
        "output_text": output_text,
        "critique_bundle": critique_bundle,
    }


VALIDATION_SCOPES: tuple[str, ...] = ('focused', 'full', 'acceptance')


def canonical_validation_plan(payload: Mapping[str, object] | None = None, **overrides: object) -> dict[str, object]:
    src: dict[str, object] = dict(payload or {})
    src.update(overrides)
    project_id = str(src.get('project_id') or '').strip()
    scope = str(src.get('validation_scope') or 'full').strip().lower()
    if scope not in VALIDATION_SCOPES:
        scope = 'full'
    commands = _coerce_string_list(src.get('commands'))
    bootstrap_required = bool(src.get('bootstrap_required', False))
    bootstrap_commands = _coerce_string_list(src.get('bootstrap_commands'))
    verification_authority_profile = str(src.get('verification_authority_profile') or 'local_plus_required_ci').strip() or 'local_plus_required_ci'
    repo_required_checks = _coerce_string_list(src.get('repo_required_checks'))
    return {
        'project_id': project_id,
        'validation_scope': scope,
        'commands': commands,
        'bootstrap_required': bootstrap_required,
        'bootstrap_commands': bootstrap_commands,
        'verification_authority_profile': verification_authority_profile,
        'repo_required_checks': repo_required_checks,
        'repo_check_contract_source': str(src.get('repo_check_contract_source') or 'project_registry'),
        'hosted_checks_source': str(src.get('hosted_checks_source') or 'gh_pr_checks'),
        'validation_plan_serializable': True,
    }


def build_project_validation_plan(project_contract: Mapping[str, object] | None = None, *, validation_scope: str = 'full') -> dict[str, object]:
    from agents.lib.project_registry import project_validation_matrix

    matrix = project_validation_matrix(project_contract)
    scope = str(validation_scope or 'full').strip().lower()
    if scope == 'focused':
        commands = list(matrix['focused_validation_commands'])
    elif scope == 'acceptance':
        commands = list(matrix['acceptance_evidence_commands'])
    else:
        scope = 'full'
        commands = list(matrix['full_validation_commands'])
    return canonical_validation_plan(
        project_id=str(matrix['project_id']),
        validation_scope=scope,
        commands=commands,
        bootstrap_required=bool(matrix['bootstrap_required']),
        bootstrap_commands=list(matrix['bootstrap_commands']),
        verification_authority_profile=str(matrix['verification_authority_profile']),
        repo_required_checks=list(matrix['repo_required_checks']),
        repo_check_contract_source=str(matrix['repo_check_contract_source']),
        hosted_checks_source=str(matrix['hosted_checks_source']),
    )


def build_validation_snapshot(
    *,
    command: str = "",
    ok: bool | None = None,
    exit_code: int | None = None,
    stdout: str = "",
    stderr: str = "",
    result: dict[str, object] | None = None,
    lint_ok: bool | None = None,
    test_ok: bool | None = None,
    branch_clean: bool | None = None,
    required_checks_passed: bool | None = None,
) -> dict[str, object]:
    source = dict(result or {})

    if any(value is not None for value in (lint_ok, test_ok, branch_clean, required_checks_passed)):
        lint_truth = True if lint_ok is None else bool(lint_ok)
        test_truth = True if test_ok is None else bool(test_ok)
        branch_truth = True if branch_clean is None else bool(branch_clean)
        required_truth = True if required_checks_passed is None else bool(required_checks_passed)
        overall_ok = lint_truth and test_truth and branch_truth and required_truth

        return {
            "command": command,
            "ok": overall_ok,
            "exit_code": 0 if overall_ok else 1,
            "stdout": stdout,
            "stderr": stderr,
            "lint_ok": lint_truth,
            "test_ok": test_truth,
            "branch_clean": branch_truth,
            "required_checks_passed": required_truth,
            "is_green": overall_ok,
        }

    if not command:
        command = str(source.get("command", ""))

    if ok is None:
        raw_ok = source.get("ok")
        if isinstance(raw_ok, bool):
            ok = raw_ok

    if exit_code is None:
        raw_exit = source.get("exit_code")
        if isinstance(raw_exit, int):
            exit_code = raw_exit

    if not stdout:
        stdout = str(source.get("stdout", ""))

    if not stderr:
        stderr = str(source.get("stderr", ""))

    if ok is None:
        ok = (exit_code == 0) if isinstance(exit_code, int) else False

    if exit_code is None:
        exit_code = 0 if ok else 1

    overall_ok = bool(ok)

    return {
        "command": command,
        "ok": overall_ok,
        "exit_code": int(exit_code),
        "stdout": stdout,
        "stderr": stderr,
        "is_green": overall_ok,
    }


def evaluate_validation_regression(
    *,
    previous: dict[str, object] | None = None,
    current: dict[str, object] | None = None,
    last_green_snapshot: dict[str, object] | None = None,
    current_snapshot: dict[str, object] | None = None,
) -> dict[str, object]:
    prev = dict(last_green_snapshot or previous or {})
    curr = dict(current_snapshot or current or {})

    def _truth(snapshot: dict[str, object]) -> bool:
        return bool(
            snapshot.get("ok", snapshot.get("is_green", False))
            and snapshot.get("lint_ok", True)
            and snapshot.get("test_ok", True)
            and snapshot.get("branch_clean", True)
            and snapshot.get("required_checks_passed", True)
        )

    prev_ok = _truth(prev)
    curr_ok = _truth(curr)
    regressed = prev_ok and not curr_ok

    regressed_dimensions: list[str] = []
    for key in ("lint_ok", "test_ok", "branch_clean", "required_checks_passed"):
        if bool(prev.get(key, True)) and not bool(curr.get(key, True)):
            regressed_dimensions.append(key)

    if regressed and not regressed_dimensions:
        regressed_dimensions.append("overall_validation")

    have_last_green = bool(prev)
    should_rollback = regressed and have_last_green
    rollback_reason = "validation_regressed_from_last_green" if should_rollback else "no_regression"

    return {
        "previous_ok": prev_ok,
        "current_ok": curr_ok,
        "regressed": regressed,
        "regressed_from_last_green": regressed,
        "last_green_available": have_last_green,
        "have_last_green": have_last_green,
        "previous_exit_code": prev.get("exit_code"),
        "current_exit_code": curr.get("exit_code"),
        "regression_reason": "validation_regressed" if regressed else "none",
        "regressed_dimensions": regressed_dimensions,
        "should_rollback_to_last_green": should_rollback,
        "rollback_reason": rollback_reason,
        "last_green_snapshot": dict(prev),
        "current_snapshot": dict(curr),
    }

def select_last_green_validation_snapshot(
    snapshots: list[dict[str, object]] | tuple[dict[str, object], ...] | None = None,
) -> dict[str, object] | None:
    items = list(snapshots or [])

    for snapshot in reversed(items):
        snap = dict(snapshot)
        is_green = bool(
            snap.get("ok", snap.get("is_green", False))
            and snap.get("lint_ok", True)
            and snap.get("test_ok", True)
            and snap.get("branch_clean", True)
            and snap.get("required_checks_passed", True)
        )
        if is_green:
            return snap

    return None
