from __future__ import annotations

import ast
import re
from typing import Any, Callable, Mapping, Sequence

from agents.lib.controller_contract import CONTROLLER_PROOF_TEST_PATHS, CONTROLLER_STRICT_MODE_PATHS
from agents.lib.task_contracts import normalize_paths, task_touches_controller_core

_SEMICOLON_RE = re.compile(r";(?=(?:[^'\"]|'[^']*'|\"[^\"]*\")*$)")
_MULTI_IMPORT_RE = re.compile(r"^\s*import\s+[^#\n]+,\s*[^#\n]+", re.MULTILINE)
_FROM_MULTI_IMPORT_RE = re.compile(r"^\s*from\s+\S+\s+import\s+[^#\n]+,\s*[^#\n]+", re.MULTILINE)
_PROOF_CLAIM_PATHS = {"README.md", "docs/TRADINGBOT_PROJECT_STATE.md", "docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md"}


def build_controller_strict_mode_context(
    *,
    required_paths: Sequence[str] | None = None,
    task_file: str = "",
) -> dict[str, Any]:
    normalized_required = normalize_paths(required_paths)
    strict_targets_touched = [
        path for path in CONTROLLER_STRICT_MODE_PATHS if path in set(normalized_required)
    ]
    enabled = task_touches_controller_core(normalized_required)
    return {
        "enabled": enabled,
        "task_file": str(task_file or "").strip(),
        "required_paths": normalized_required,
        "strict_targets_touched": strict_targets_touched,
        "focused_test_paths": list(CONTROLLER_PROOF_TEST_PATHS),
    }


def controller_strict_mode_directives(context: Mapping[str, Any] | None) -> str:
    payload = dict(context or {})
    if not payload.get("enabled"):
        return ""
    touched = payload.get("strict_targets_touched") or []
    lines = [
        "Controller strict mode is active for this task.",
        "Keep controller patches readable and conventional. Do not minify code, compress many statements onto one line, or combine imports mechanically.",
        "Preserve controller contract vocabulary and persisted truth fields exactly.",
        "Docs or README proof claims are not considered complete unless focused controller proof tests are green.",
    ]
    if touched:
        lines.append("Controller strict-mode targets touched: " + ", ".join(str(item) for item in touched))
    return "\n".join(lines)


def _semicolon_density_issue(path: str, content: str) -> str | None:
    bad_lines: list[int] = []
    total_semicolons = 0
    for lineno, raw in enumerate(str(content or "").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        semicolons = len(_SEMICOLON_RE.findall(raw))
        if semicolons:
            total_semicolons += semicolons
            if semicolons >= 1:
                bad_lines.append(lineno)
    if total_semicolons >= 5 or len(bad_lines) >= 3:
        shown = ", ".join(str(i) for i in bad_lines[:6])
        return (
            f"{path}: controller strict mode rejected clustered one-line statements/semicolon density "
            f"(semicolons={total_semicolons}, lines={shown})."
        )
    return None


def _compressed_import_issue(path: str, content: str) -> str | None:
    import_hits = len(_MULTI_IMPORT_RE.findall(content))
    from_hits = len(_FROM_MULTI_IMPORT_RE.findall(content))
    if import_hits + from_hits >= 2:
        return (
            f"{path}: controller strict mode rejected compressed multi-import formatting "
            f"(import_lines={import_hits}, from_import_lines={from_hits})."
        )
    return None


def _unused_import_names(path: str, content: str) -> list[str]:
    try:
        tree = ast.parse(content, filename=path)
    except SyntaxError:
        return []

    imported: dict[str, str] = {}
    used: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import) -> Any:
            for alias in node.names:
                name = (alias.asname or alias.name.split(".", 1)[0]).strip()
                if name:
                    imported[name] = alias.name

        def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
            for alias in node.names:
                if alias.name == "*":
                    continue
                name = (alias.asname or alias.name).strip()
                if name:
                    imported[name] = alias.name

        def visit_Name(self, node: ast.Name) -> Any:
            used.add(node.id)

    Visitor().visit(tree)
    return sorted(name for name in imported if name not in used and not name.startswith("_"))


def _unused_import_churn_issue(path: str, content: str) -> str | None:
    unused = _unused_import_names(path, content)
    if len(unused) >= 3:
        return (
            f"{path}: controller strict mode rejected likely mechanical unused-import churn "
            f"({', '.join(unused[:6])})."
        )
    return None


def _minified_format_issue(path: str, content: str) -> str | None:
    lines = str(content or "").splitlines()
    nonblank = [line for line in lines if line.strip()]
    if len(nonblank) < 20:
        return None
    blank_count = len(lines) - len(nonblank)
    avg_length = sum(len(line) for line in nonblank) / max(1, len(nonblank))
    long_lines = [line for line in nonblank if len(line) >= 180]
    if blank_count == 0 and (avg_length >= 110 or len(long_lines) >= 4):
        return (
            f"{path}: controller strict mode rejected suspicious minified formatting "
            f"(avg_line_length={avg_length:.1f}, long_lines={len(long_lines)})."
        )
    return None


def controller_strict_preapply_issues(
    bundle: Mapping[str, str] | None,
    *,
    touched_paths: Sequence[str] | None = None,
) -> list[str]:
    files = dict(bundle or {})
    touched = set(normalize_paths(touched_paths))
    controller_paths = [
        path for path in files if path in set(CONTROLLER_STRICT_MODE_PATHS) and (not touched or path in touched)
    ]
    issues: list[str] = []
    for path in controller_paths:
        content = str(files.get(path, "") or "")
        for issue in (
            _semicolon_density_issue(path, content),
            _compressed_import_issue(path, content),
            _minified_format_issue(path, content),
            _unused_import_churn_issue(path, content),
        ):
            if issue:
                issues.append(issue)
    deduped: list[str] = []
    seen: set[str] = set()
    for issue in issues:
        if issue not in seen:
            deduped.append(issue)
            seen.add(issue)
    return deduped


def format_controller_strict_preapply_issues(issues: Sequence[str] | None) -> str:
    entries = [str(issue).strip() for issue in (issues or []) if str(issue).strip()]
    if not entries:
        return ""
    return (
        "Controller strict mode rejected low-discipline generated patch before apply:\n"
        + "\n".join(f"- {entry}" for entry in entries)
    )


def _result_output(result: object) -> str:
    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    merged = f"{stdout}{stderr}"
    return str(merged).strip()


def _proof_claims_deferred_message(changed_paths: Sequence[str] | None, *, focused_ok: bool) -> str:
    touched = set(normalize_paths(changed_paths))
    if focused_ok or not touched.intersection(_PROOF_CLAIM_PATHS):
        return ""
    return "Docs/README proof-complete claims remain deferred until focused controller proof tests are green."


def run_controller_strict_checks(
    *,
    capture_result: Callable[[list[str]], object],
    changed_paths: Sequence[str] | None = None,
    focused_test_paths: Sequence[str] | None = None,
) -> dict[str, Any]:
    proof_tests = list(focused_test_paths or CONTROLLER_PROOF_TEST_PATHS)
    focused_cmd = ["pytest", "-q", *proof_tests]
    focused = capture_result(focused_cmd)
    focused_ok = int(getattr(focused, "returncode", 1)) == 0
    focused_output = _result_output(focused)
    deferred = _proof_claims_deferred_message(changed_paths, focused_ok=focused_ok)
    if not focused_ok:
        parts = ["=== controller proof tests ==="]
        if focused_output:
            parts.append(focused_output)
        if deferred:
            parts.append(deferred)
        return {
            "strict_mode": True,
            "controller_proof_tests_passed": False,
            "focused_ok": False,
            "lint_ok": False,
            "test_ok": False,
            "proof_claims_deferred": bool(deferred),
            "proof_claims_deferred_message": deferred,
            "output_text": "\n\n".join(part for part in parts if part).strip(),
        }

    ruff = capture_result(["ruff", "check", "."])
    lint_ok = int(getattr(ruff, "returncode", 1)) == 0
    ruff_output = _result_output(ruff)

    pytest_all = capture_result(["pytest", "-q"])
    test_ok = int(getattr(pytest_all, "returncode", 1)) == 0
    pytest_output = _result_output(pytest_all)

    parts: list[str] = []
    if not lint_ok:
        parts.extend(["=== ruff check . ===", ruff_output])
    if not test_ok:
        parts.extend(["=== pytest -q ===", pytest_output])
    return {
        "strict_mode": True,
        "controller_proof_tests_passed": True,
        "focused_ok": True,
        "lint_ok": lint_ok,
        "test_ok": test_ok,
        "proof_claims_deferred": False,
        "proof_claims_deferred_message": "",
        "output_text": "\n\n".join(part for part in parts if part).strip(),
    }
