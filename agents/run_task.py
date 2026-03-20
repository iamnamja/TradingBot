#!/usr/bin/env python3
"""Agent task runner.

Reads a task markdown file, asks an LLM to output a deterministic file bundle,
writes files, runs ruff+pytest, and optionally commits/pushes to an agent branch.

File bundle format (MUST be exact):

BEGIN_FILE_BUNDLE
FILE: path/relative/to/repo.py
<file contents>
END_FILE
END_FILE_BUNDLE

Empty bundle is allowed:
BEGIN_FILE_BUNDLE
END_FILE_BUNDLE
"""

from __future__ import annotations

import argparse
import ast
import difflib
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

FILE_BUNDLE_BEGIN = "BEGIN_FILE_BUNDLE"
FILE_BUNDLE_END = "END_FILE_BUNDLE"
FILE_BEGIN_PREFIX = "FILE:"
FILE_END = "END_FILE"

DELIVERABLE_PATH_RE = re.compile(r"`([^`]+\.[A-Za-z0-9_]+)`")
FILE_HEADER_RE = re.compile(r"^\s*(?:#\s*)?FILE:\s*(.+?)\s*$")
RUNNER_METHOD_HEADER_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)
TASK_FILE_POLICY_RE = re.compile(r"^\s*-\s*FILE:\s*(?P<path>\S+)(?P<rest>.*)$")
TASK_FILE_ATTR_RE = re.compile(r"([A-Z_]+)=([^\s]+)")
CONTRACT_DIRECTIVE_RE = re.compile(r"^\s*-\s*(CONSTRUCTOR|CONFIG_WRAPPER|ALLOWED_METHODS|FORBID_IMPORTS|FORBID_CALLS|RESULT_KEYS):\s*(.+)$")

RUFF_UNUSED_IMPORT_RE = re.compile(r"F401 .*? --> ([^\n:]+):(\d+):\d+", re.MULTILINE)
RUFF_BOOL_COMPARE_RE = re.compile(r"E712 .*? --> ([^\n:]+):(\d+):\d+", re.MULTILINE)
RUFF_UNDEFINED_NAME_RE = re.compile(r"F821 Undefined name `([^`]+)`", re.MULTILINE)

PYTEST_TEST_NAME_RE = re.compile(r"_{5,}\s*(.*?)\s*_{5,}")
PYTEST_TEST_FILE_RE = re.compile(r"^(tests[\\/][^\n:]+):(\d+):", re.MULTILINE)
PYTEST_EXACT_MISMATCH_RE = re.compile(r"^E\s+assert\s+(.+?)\s+==\s+(.+)$", re.MULTILINE)

MISSING_ATTR_RE = re.compile(r"AttributeError: '([^']+)' object has no attribute '([^']+)'")
MODULE_NOT_FOUND_RE = re.compile(r"ModuleNotFoundError: No module named '([^']+)'")
NAME_ERROR_RE = re.compile(r"NameError: name '([^']+)' is not defined")
KEY_ERROR_RE = re.compile(r"KeyError: '([^']+)'")
WIN_ECHO_RE = re.compile(r"FileNotFoundError: \[WinError 2\]", re.MULTILINE)


class FileBundleError(ValueError):
    pass


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv()


def default_provider() -> str:
    provider = os.getenv("TRADINGBOT_AGENT_PROVIDER", "").strip().lower()
    if provider:
        return provider
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY", "").strip():
        return "anthropic"
    return "openai"


def default_model_for_provider(provider: str) -> str:
    env_model = os.getenv("TRADINGBOT_AGENT_MODEL", "").strip()
    if env_model:
        return env_model
    if provider == "openai":
        return "gpt-5"
    return "claude-sonnet-4-5"


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


def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=False)


def capture(cmd: List[str]) -> str:
    cp = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return cp.stdout.strip()


def capture_result(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def ensure_clean_worktree() -> None:
    if capture(["git", "status", "--porcelain"]).strip():
        raise RuntimeError("Working tree is not clean. Commit/stash your changes before running the agent.")


def ensure_branch(branch: str) -> None:
    cur = capture(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if cur == branch:
        return
    if capture(["git", "branch", "--list", branch]).strip():
        run(["git", "switch", branch])
    else:
        run(["git", "switch", "-c", branch])


def normalize_newlines(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"^\ufeff", "", s)


def parse_file_bundle(text: str) -> Dict[str, str]:
    text = normalize_newlines(text)

    if FILE_BUNDLE_BEGIN not in text or FILE_BUNDLE_END not in text:
        raise FileBundleError("Model output missing BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers.")

    start = text.index(FILE_BUNDLE_BEGIN) + len(FILE_BUNDLE_BEGIN)
    end = text.index(FILE_BUNDLE_END)
    body = text[start:end].strip("\n")

    if not body.strip():
        return {}

    if "FILE:" not in body:
        raise FileBundleError("No FILE: headers found inside file bundle.")

    files: Dict[str, str] = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        m = FILE_HEADER_RE.match(lines[i])
        if not m:
            i += 1
            continue

        relpath = m.group(1).strip()
        if not relpath:
            raise FileBundleError("Empty FILE: path.")

        i += 1
        buf: List[str] = []
        while i < len(lines) and lines[i].strip("\n") != FILE_END:
            if FILE_HEADER_RE.match(lines[i]):
                raise FileBundleError(
                    f"Nested FILE header encountered before END_FILE for {relpath}. "
                    "Every FILE block must be closed with END_FILE before the next FILE header."
                )
            buf.append(lines[i])
            i += 1
        if i >= len(lines):
            raise FileBundleError(f"Missing END_FILE for {relpath}.")

        i += 1
        files[relpath] = "\n".join(buf).rstrip("\n") + "\n"

    if not files:
        raise FileBundleError("No FILE: blocks could be parsed (check FILE:/END_FILE lines).")

    return files


def write_files(files: Dict[str, str]) -> None:
    repo_root = Path(".").resolve()
    for rel, data in files.items():
        path = (repo_root / rel).resolve()
        if not str(path).startswith(str(repo_root)):
            raise ValueError(f"Refusing to write outside repo root: {rel}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8", newline="\n")


def _deliverables_section(task_text: str) -> str:
    task_text = normalize_newlines(task_text)
    lines = task_text.split("\n")

    start_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped in {"## deliverables", "# deliverables"}:
            start_idx = i
            break

    if start_idx is None:
        return task_text

    collected = [lines[start_idx]]
    for line in lines[start_idx + 1:]:
        if re.match(r"^##\s+", line):
            break
        collected.append(line)

    return "\n".join(collected)

def parse_required_files(task_text: str) -> List[str]:
    section = _deliverables_section(task_text)

    req: List[str] = []
    for m in DELIVERABLE_PATH_RE.finditer(section):
        path = m.group(1).strip().replace("\\", "/")
        if "/" in path and path.startswith(("src/", "tests/", "agents/")):
            req.append(path)

    seen = set()
    out: List[str] = []
    for p in req:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out

def task_requires_material_update(task_text: str) -> bool:
    lower = normalize_newlines(task_text).lower()
    phrases = [
        "must create or update",
        "must be created/updated",
        "must be updated",
        "must be materially updated",
        "materially updated in the same bundle",
        "required deliverables were included but not materially updated",
    ]
    return any(p in lower for p in phrases)


def task_allows_unchanged_cli(task_text: str) -> bool:
    lower = normalize_newlines(task_text).lower()
    phrases = [
        "not blocked solely because `cli.py` is unchanged",
        "not blocked solely because cli.py is unchanged",
        "including the current compatible `cli.py` in the bundle is acceptable",
        "including the current compatible cli.py in the bundle is acceptable",
        "do not force unnecessary churn in `cli.py`",
        "do not force unnecessary churn in cli.py",
    ]
    return any(p in lower for p in phrases)



def _normalize_anchor_token(token: str) -> str:
    token = token.strip().strip("`")
    if not token:
        return token
    if token.startswith("def "):
        return token
    if token.endswith("("):
        return f"def {token}"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
        return f"def {token}("
    return token



def _iter_markdown_sections(task_text: str) -> List[Tuple[str, List[str]]]:
    text = normalize_newlines(task_text)
    lines = text.split("\n")
    sections: List[Tuple[str, List[str]]] = []
    current_name = ""
    current_lines: List[str] = []
    for line in lines:
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*$", line)
        if heading:
            sections.append((current_name, current_lines))
            current_name = heading.group(1).strip().lower()
            current_lines = []
        else:
            current_lines.append(line)
    sections.append((current_name, current_lines))
    return sections


def parse_harness_file_policies(task_text: str) -> Dict[str, Dict[str, object]]:
    """Parse machine-readable harness policies from task text."""
    policies: Dict[str, Dict[str, object]] = {}
    allowed_section_names = {
        "deliverables",
        "harness policy",
        "machine-readable contract directives",
    }

    def _add_rule(path: str, rule: str) -> None:
        path = path.strip().replace("\\", "/")
        if not path or not rule:
            return
        entry = policies.setdefault(path, {"rules": []})
        rules = entry.setdefault("rules", [])
        if isinstance(rules, list):
            rules.append(rule)

    for section_name, section_lines in _iter_markdown_sections(task_text):
        parse_file_directives = section_name in allowed_section_names
        for raw_line in section_lines:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("HARNESS_POLICY:"):
                try:
                    _, rest = line.split("HARNESS_POLICY:", 1)
                    path_and_rule = rest.strip()
                    path, rule = path_and_rule.split(None, 1)
                except ValueError:
                    continue
                _add_rule(path, rule.strip())
                continue

            if not parse_file_directives:
                continue

            m = TASK_FILE_POLICY_RE.match(line)
            if not m:
                continue
            if "MODE=" not in line:
                continue
            path = m.group("path").strip().replace("\\", "/")
            attrs = dict(TASK_FILE_ATTR_RE.findall((m.group("rest") or "").strip()))
            mode = attrs.get("MODE", "").strip().upper()
            if not path or not mode:
                continue
            if mode == "PROTECTED_FORBID":
                _add_rule(path, "forbid")
            elif mode == "EXACT_COPY":
                _add_rule(path, "exact_copy")
            elif mode == "EXACT_COPY_PLUS_APPEND_METHOD":
                anchor = attrs.get("ANCHOR_BEFORE", "").strip()
                if anchor:
                    _add_rule(path, f"append_before:{_normalize_anchor_token(anchor)}")
                allow_method = attrs.get("ALLOW_NEW_METHOD", "").strip()
                if allow_method:
                    _add_rule(path, f"allow_methods:{allow_method}")
                max_changed = attrs.get("MAX_CHANGED_LINES", "").strip()
                if max_changed:
                    _add_rule(path, f"max_changed_lines:{max_changed}")
            elif mode == "EXACT_COPY_PLUS_REPLACE_METHOD":
                replace_method = (
                    attrs.get("TARGET_METHOD", "").strip()
                    or attrs.get("REPLACE_METHOD", "").strip()
                    or attrs.get("ALLOW_EXISTING_METHOD", "").strip()
                )
                if replace_method:
                    _add_rule(path, f"replace_method:{replace_method}")
                    _add_rule(path, f"allow_methods:{replace_method}")
                max_changed = attrs.get("MAX_CHANGED_LINES", "").strip()
                if max_changed:
                    _add_rule(path, f"max_changed_lines:{max_changed}")
            elif mode == "METHOD_ADD_ONLY":
                allow_method = attrs.get("ALLOW_NEW_METHOD", "").strip()
                if allow_method:
                    _add_rule(path, f"allow_methods:{allow_method}")
                max_changed = attrs.get("MAX_CHANGED_LINES", "").strip()
                if max_changed:
                    _add_rule(path, f"max_changed_lines:{max_changed}")
    return policies


def _extract_protected_method_targets(task_text: str) -> List[Dict[str, object]]:
    targets: List[Dict[str, object]] = []
    for path, config in parse_harness_file_policies(task_text).items():
        rules = config.get("rules", [])
        if not isinstance(rules, list):
            continue
        anchor = None
        append_method = None
        replace_method = None
        max_changed_lines = None
        for rule in rules:
            if not isinstance(rule, str):
                continue
            if rule.startswith("append_before:"):
                anchor = rule.split("append_before:", 1)[1]
            elif rule.startswith("replace_method:"):
                replace_method = rule.split("replace_method:", 1)[1].strip()
            elif rule.startswith("allow_methods:") and append_method is None and replace_method is None:
                methods = [x.strip() for x in rule.split("allow_methods:", 1)[1].split(",") if x.strip()]
                if len(methods) == 1:
                    append_method = methods[0]
            elif rule.startswith("max_changed_lines:"):
                try:
                    max_changed_lines = int(rule.split("max_changed_lines:", 1)[1].strip())
                except ValueError:
                    pass
        if anchor and append_method:
            targets.append({
                "path": path,
                "mode": "append",
                "anchor": anchor,
                "method_name": append_method,
                "max_changed_lines": max_changed_lines,
            })
        elif replace_method:
            targets.append({
                "path": path,
                "mode": "replace",
                "method_name": replace_method,
                "max_changed_lines": max_changed_lines,
            })
    return targets
def _count_changed_lines(old: str, new: str) -> int:
    diff = difflib.unified_diff(
        normalize_newlines(old).splitlines(),
        normalize_newlines(new).splitlines(),
        lineterm="",
    )
    changed = 0
    for line in diff:
        if not line:
            continue
        if line.startswith(("---", "+++", "@@")):
            continue
        if line.startswith("+") or line.startswith("-"):
            changed += 1
    return changed


def enforce_harness_file_policies(task_text: str, bundle: Dict[str, str], baseline: Dict[str, str]) -> Tuple[bool, str]:
    issues: List[str] = []
    policies = parse_harness_file_policies(task_text)
    for path, config in policies.items():
        rules = config.get("rules", [])
        if not isinstance(rules, list):
            continue
        proposed = bundle.get(path)
        original = baseline.get(path)
        for rule in rules:
            if not isinstance(rule, str):
                continue
            if rule == "forbid":
                if proposed is not None and original is not None and normalize_newlines(proposed) != normalize_newlines(original):
                    issues.append(f"`{path}` is protected by `forbid` and must not change.")
                elif proposed is not None and original is None:
                    issues.append(f"`{path}` is protected by `forbid` and must not be created.")
                continue
            if rule == "exact_copy":
                if proposed is None:
                    issues.append(f"`{path}` is protected by `exact_copy` and must be emitted unchanged.")
                elif original is None:
                    issues.append(f"`{path}` is protected by `exact_copy`, but no baseline file exists.")
                elif normalize_newlines(proposed) != normalize_newlines(original):
                    issues.append(f"`{path}` is protected by `exact_copy` and changed unexpectedly.")
                continue
            if rule.startswith("append_before:"):
                if proposed is None:
                    issues.append(f"`{path}` is protected by `append_before`, but the file was omitted from the bundle.")
                    continue
                if original is None:
                    issues.append(f"`{path}` is protected by `append_before`, but no baseline file exists.")
                    continue
                anchor = rule.split("append_before:", 1)[1]
                if anchor not in original:
                    issues.append(f"Harness anchor `{anchor}` not found in baseline `{path}`.")
                    continue
                if anchor not in proposed:
                    issues.append(f"`{path}` changed content at or after protected anchor `{anchor}`. Only additive insertion before the anchor is allowed.")
                    continue
                original_before, original_after = original.split(anchor, 1)
                proposed_before, proposed_after = proposed.split(anchor, 1)
                if normalize_newlines(proposed_after) != normalize_newlines(original_after):
                    issues.append(f"`{path}` changed content at or after protected anchor `{anchor}`. Only additive insertion before the anchor is allowed.")
                    continue
                if normalize_newlines(proposed_before) == normalize_newlines(original_before):
                    issues.append(f"`{path}` is protected by `append_before:{anchor}`, but no additive insertion before the anchor was detected.")
                continue
            if rule.startswith("max_changed_lines:"):
                if proposed is None or original is None:
                    continue
                raw_limit = rule.split("max_changed_lines:", 1)[1].strip()
                try:
                    limit = int(raw_limit)
                except ValueError:
                    issues.append(f"`{path}` has invalid `max_changed_lines` value `{raw_limit}`.")
                    continue
                changed = _count_changed_lines(original, proposed)
                if changed > limit:
                    issues.append(f"`{path}` exceeded max changed lines policy ({changed} > {limit}).")
                continue
            if rule.startswith("allow_methods:"):
                if proposed is None or original is None:
                    continue
                allowed = {name.strip() for name in rule.split("allow_methods:", 1)[1].split(",") if name.strip()}
                original_methods = set(RUNNER_METHOD_HEADER_RE.findall(original))
                proposed_methods = set(RUNNER_METHOD_HEADER_RE.findall(proposed))
                removed = original_methods - proposed_methods
                added = proposed_methods - original_methods
                disallowed_added = sorted(name for name in added if name not in allowed)
                if removed:
                    issues.append(f"`{path}` removed existing methods under `allow_methods` policy: {', '.join(sorted(removed))}.")
                if disallowed_added:
                    issues.append(f"`{path}` added disallowed methods under `allow_methods` policy: {', '.join(disallowed_added)}.")
                continue
    if issues:
        return False, "Harness protected-file policy violations detected:\n" + "\n".join(f"- {x}" for x in issues)
    return True, ""


def _method_indent_from_anchor_content(content: str, anchor: str) -> str:
    idx = content.find(anchor)
    if idx < 0:
        return "    "
    line_start = content.rfind("\n", 0, idx) + 1
    line_end = content.find("\n", idx)
    if line_end < 0:
        line_end = len(content)
    line = content[line_start:line_end]
    return line[: len(line) - len(line.lstrip())]


def _method_relative_body_indent(lines: List[str]) -> int:
    non_empty = [line.expandtabs(4) for line in lines if line.strip()]
    if not non_empty:
        return 0
    return min(len(line) - len(line.lstrip(" ")) for line in non_empty)


def _indent_method_text(method_text: str, indent: str) -> str:
    raw = normalize_newlines(method_text).strip("\n")
    if not raw:
        raise FileBundleError("Method insertion payload was empty.")
    lines = raw.split("\n")
    first = lines[0].lstrip()
    if not first.startswith("def "):
        raise FileBundleError("Method insertion payload must begin with a def line.")
    rest = [line.expandtabs(4) for line in lines[1:]]
    base = _method_relative_body_indent(rest)
    out = [indent + first]
    for line in rest:
        if not line.strip():
            out.append("")
            continue
        rel = line[base:] if len(line) >= base else line.lstrip()
        out.append(indent + "    " + rel)
    return "\n".join(out).rstrip("\n") + "\n"


def apply_method_insertion(original: str, anchor: str, method_name: str, method_text: str) -> str:
    if anchor not in original:
        raise FileBundleError(f"Insertion anchor `{anchor}` not found in baseline file.")
    method_names = RUNNER_METHOD_HEADER_RE.findall(method_text)
    if method_names != [method_name]:
        raise FileBundleError(f"Method insertion payload must define exactly one method `{method_name}`; got {method_names or 'none'}.")
    indent = _method_indent_from_anchor_content(original, anchor)
    inserted = _indent_method_text(method_text, indent)
    anchor_idx = original.index(anchor)
    insert_at = original.rfind("\n", 0, anchor_idx) + 1
    before = original[:insert_at]
    after = original[insert_at:]
    if before and not before.endswith("\n\n"):
        before = before + ("\n" if before.endswith("\n") else "\n\n")
    return before + inserted + "\n" + after


def apply_method_replacement(original: str, method_name: str, method_text: str) -> str:
    method_names = RUNNER_METHOD_HEADER_RE.findall(method_text)
    if method_names != [method_name]:
        raise FileBundleError(f"Method insertion payload must define exactly one method `{method_name}`; got {method_names or 'none'}.")
    content = normalize_newlines(original)
    lines = content.split("\n")
    start_idx = None
    method_indent = 0
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(f"def {method_name}("):
            start_idx = idx
            method_indent = len(line) - len(stripped)
            break
    if start_idx is None:
        raise FileBundleError(f"Could not locate existing method `{method_name}` in baseline file.")
    end_idx = len(lines)
    for idx in range(start_idx + 1, len(lines)):
        stripped = lines[idx].lstrip()
        if not stripped:
            continue
        cur_indent = len(lines[idx]) - len(stripped)
        if cur_indent <= method_indent and stripped.startswith("def "):
            end_idx = idx
            break
    indent = lines[start_idx][:method_indent]
    replacement_lines = _indent_method_text(method_text, indent).rstrip("\n").split("\n")
    new_lines = lines[:start_idx] + replacement_lines + lines[end_idx:]
    return "\n".join(new_lines).rstrip("\n") + "\n"


METHOD_INSERTION_BEGIN = "BEGIN_METHOD_INSERTION"
METHOD_INSERTION_END = "END_METHOD_INSERTION"
METHOD_BLOCK_BEGIN = "BEGIN_METHOD"
METHOD_BLOCK_END = "END_METHOD"


def _method_block_from_file_content(file_content: str, method_name: str) -> str:
    content = normalize_newlines(file_content)
    lines = content.split("\n")
    start_idx = None
    method_indent = 0
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(f"def {method_name}("):
            start_idx = idx
            method_indent = len(line) - len(stripped)
            break
    if start_idx is None:
        raise FileBundleError(f"Could not locate method `{method_name}` in file content.")
    end_idx = len(lines)
    for idx in range(start_idx + 1, len(lines)):
        stripped = lines[idx].lstrip()
        if not stripped:
            continue
        cur_indent = len(lines[idx]) - len(stripped)
        if cur_indent <= method_indent and stripped.startswith("def "):
            end_idx = idx
            break
    return "\n".join(lines[start_idx:end_idx]).rstrip("\n") + "\n"


def parse_method_insertion_bundle(text: str, expected_path: str, expected_method_name: str) -> str:
    text = normalize_newlines(text)
    lines = text.split("\n")

    begin_idx = next((i for i, line in enumerate(lines) if line.strip() == METHOD_INSERTION_BEGIN), None)
    if begin_idx is not None:
        end_idx = next((i for i in range(begin_idx + 1, len(lines)) if lines[i].strip() == METHOD_INSERTION_END), None)
        if end_idx is None:
            raise FileBundleError("Missing END_METHOD_INSERTION in method insertion bundle.")

        body_lines = lines[begin_idx + 1:end_idx]
        target_file = None
        method_name = None
        i = 0
        while i < len(body_lines):
            line = body_lines[i].strip()
            if line.startswith("TARGET_FILE:"):
                target_file = line.split(":", 1)[1].strip().replace("\\", "/")
            elif line.startswith("METHOD_NAME:"):
                method_name = line.split(":", 1)[1].strip()
            elif line == METHOD_BLOCK_BEGIN:
                i += 1
                buf: List[str] = []
                while i < len(body_lines) and body_lines[i].strip() != METHOD_BLOCK_END:
                    buf.append(body_lines[i])
                    i += 1
                if i >= len(body_lines):
                    raise FileBundleError("Missing END_METHOD in method insertion bundle.")
                if target_file and target_file != expected_path:
                    raise FileBundleError(f"Method insertion target file mismatch: expected {expected_path}, got {target_file}.")
                if method_name and method_name != expected_method_name:
                    raise FileBundleError(f"Method insertion method mismatch: expected {expected_method_name}, got {method_name}.")
                return "\n".join(buf).rstrip("\n") + "\n"
            i += 1

    files = parse_file_bundle(text)
    if expected_path not in files:
        raise FileBundleError("Method insertion response did not include protected target file or insertion markers.")
    return _method_block_from_file_content(files[expected_path], expected_method_name)


def build_method_insertion_messages(task_text: str, target_path: str, method_name: str, baseline_content: str, mode: str, extra_directives: str = "", anchor: str = "") -> List[dict]:
    operation_line = (
        f"Replace the existing method named `{method_name}` in place."
        if mode == "replace"
        else f"Add exactly one new method named `{method_name}` before anchor `{anchor}`."
    )
    parts = [
        task_text.rstrip(),
        "",
        "## Protected-file method mode",
        f"Return ONLY a method insertion bundle for `{target_path}`.",
        operation_line,
        "You are editing the EXISTING harness file in place.",
        "Do not rewrite the full file.",
        "Do not include any other file in this response.",
        "Do not replace the current harness with a miniature standalone script.",
        "Preserve the current module structure, imports, entrypoint, and unrelated functions exactly.",
        "Only perform the requested method append or method replacement.",
        "The response will be rejected unless it contains exactly one `def` total, and that `def` is the requested method.",
        "",
        "Required format:",
        "BEGIN_METHOD_INSERTION",
        f"TARGET_FILE: {target_path}",
        f"METHOD_NAME: {method_name}",
        "BEGIN_METHOD",
        f"def {method_name}(...):",
        "    ...",
        "END_METHOD",
        "END_METHOD_INSERTION",
        "",
        "## Current baseline file content",
        f"FILE: {target_path}",
        baseline_content.rstrip("\n"),
        "END_FILE",
    ]
    if extra_directives.strip():
        parts.extend(["", "## Iteration-specific directives", extra_directives.strip()])
    return [
        {"role": "system", "content": load_system_prompt().strip()},
        {"role": "user", "content": "\n".join(parts).rstrip() + "\n"},
    ]


def request_and_parse_method_insertion(messages: List[dict], model: str, provider: str, last_output_path: Path, expected_path: str, expected_method_name: str) -> str:
    out = chat(messages, model=model, provider=provider)
    last_output_path.write_text(out + "\n", encoding="utf-8", newline="\n")
    try:
        return parse_method_insertion_bundle(out, expected_path, expected_method_name)
    except Exception as exc:
        first_error = str(exc)

    reminder = (
        "Your previous response was INVALID.\n"
        "You MUST output ONLY a valid method insertion bundle using the literal markers below.\n"
        "Do not output BEGIN_FILE_BUNDLE for this protected file.\n"
        "Do not add any extra top-level def.\n\n"
        "BEGIN_METHOD_INSERTION\n"
        f"TARGET_FILE: {expected_path}\n"
        f"METHOD_NAME: {expected_method_name}\n"
        "BEGIN_METHOD\n"
        f"def {expected_method_name}(...):\n"
        "    ...\n"
        "END_METHOD\n"
        "END_METHOD_INSERTION\n\n"
        f"Parser error: {first_error}"
    )
    out2 = chat(messages + [{"role": "user", "content": reminder}], model=model, provider=provider)
    last_output_path.write_text(out2 + "\n", encoding="utf-8", newline="\n")
    retry_error = None
    try:
        return parse_method_insertion_bundle(out2, expected_path, expected_method_name)
    except Exception as exc:
        retry_error = str(exc)

    recovered_lines = normalize_newlines(out2).split("\n")
    start_candidates = [
        idx for idx, line in enumerate(recovered_lines)
        if (len(line) - len(line.lstrip())) == 0 and line.startswith(f"def {expected_method_name}(")
    ]
    if not start_candidates:
        raise FileBundleError(f"Model returned malformed method insertion bundle after retry: {retry_error}; raw-text recovery failed: zero matching method definitions were found.")
    if len(start_candidates) > 1:
        raise FileBundleError(f"Model returned malformed method insertion bundle after retry: {retry_error}; raw-text recovery failed: more than one matching method definition was found.")

    start_idx = start_candidates[0]
    end_idx = len(recovered_lines)
    for idx in range(start_idx + 1, len(recovered_lines)):
        stripped = recovered_lines[idx].strip()
        cur_indent = len(recovered_lines[idx]) - len(recovered_lines[idx].lstrip())
        if stripped in {METHOD_BLOCK_END, METHOD_INSERTION_END, FILE_END, FILE_BUNDLE_BEGIN, FILE_BUNDLE_END, METHOD_INSERTION_BEGIN}:
            end_idx = idx
            break
        if FILE_HEADER_RE.match(recovered_lines[idx]):
            end_idx = idx
            break
        if cur_indent == 0 and stripped.startswith("def "):
            end_idx = idx
            break
    method_text = "\n".join(recovered_lines[start_idx:end_idx]).rstrip("\n") + "\n"
    if RUNNER_METHOD_HEADER_RE.findall(method_text) != [expected_method_name]:
        raise FileBundleError(f"Model returned malformed method insertion bundle after retry: {retry_error}; raw-text recovery failed: recovered method would violate the single-method insertion rule.")
    try:
        ast.parse(method_text, filename=expected_path)
    except SyntaxError as exc:
        raise FileBundleError(f"Model returned malformed method insertion bundle after retry: {retry_error}; raw-text recovery failed: recovered method body has Python syntax error at line {exc.lineno or 0}: {exc.msg or 'invalid syntax'}.") from exc
    return method_text
def validate_python_syntax(bundle: Dict[str, str]) -> Tuple[bool, str]:
    issues: List[str] = []
    for rel, content in bundle.items():
        if not rel.endswith(".py"):
            continue
        try:
            ast.parse(normalize_newlines(content), filename=rel)
        except SyntaxError as exc:
            lineno = exc.lineno or 0
            msg = exc.msg or "invalid syntax"
            issues.append(f"`{rel}` has Python syntax error at line {lineno}: {msg}")
    if issues:
        return False, "Python syntax validation failed:\n" + "\n".join(f"- {x}" for x in issues)
    return True, ""
def _append_task_feedback(task_text: str, message: str) -> str:
    return task_text.rstrip() + "\n\nIMPORTANT: " + message + "\n"


def _repeat_limit_exceeded(counter: Dict[str, int], key: str, limit: int) -> bool:
    counter[key] = counter.get(key, 0) + 1
    return counter[key] >= limit


def existing_file_contents(paths: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for p in paths:
        path = Path(p)
        if path.exists() and path.is_file():
            out[p] = path.read_text(encoding="utf-8", errors="replace")
    return out


def snapshot_file_contents(paths: List[str]) -> Dict[str, str | None]:
    snapshot: Dict[str, str | None] = {}
    repo_root = Path(".").resolve()
    for rel in paths:
        path = (repo_root / rel).resolve()
        if not str(path).startswith(str(repo_root)):
            continue
        if path.exists() and path.is_file():
            snapshot[rel] = path.read_text(encoding="utf-8", errors="replace")
        else:
            snapshot[rel] = None
    return snapshot


def restore_file_snapshot(snapshot: Dict[str, str | None]) -> None:
    repo_root = Path(".").resolve()
    for rel, previous in snapshot.items():
        path = (repo_root / rel).resolve()
        if not str(path).startswith(str(repo_root)):
            continue
        if previous is None:
            if path.exists():
                path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(previous, encoding="utf-8", newline="\n")


def parse_required_runner_methods(task_text: str) -> List[str]:
    lower = normalize_newlines(task_text).lower()
    methods: List[str] = []
    for method in [
        "select_next_task",
        "run_next_task",
        "execute_task",
        "process_execution_result",
        "simulate_backlog",
        "translate_to_orchestrator_behavior",
    ]:
        if method in lower:
            methods.append(method)

    seen = set()
    out: List[str] = []
    for method in methods:
        if method not in seen:
            out.append(method)
            seen.add(method)
    return out



def parse_task_contract_directives(task_text: str) -> Dict[str, List[str]]:
    directives: Dict[str, List[str]] = {}
    allowed_sections = {"", "machine-readable contract directives", "critical", "current runner baseline — must match exactly"}
    for section_name, section_lines in _iter_markdown_sections(task_text):
        if section_name not in allowed_sections and "contract" not in section_name:
            continue
        for raw_line in section_lines:
            m = CONTRACT_DIRECTIVE_RE.match(raw_line)
            if not m:
                continue
            key = m.group(1).strip().upper()
            value = m.group(2).strip()
            directives.setdefault(key, []).append(value)
    return directives


def _module_source_for_name(mod: str, bundle: Dict[str, str]) -> str | None:
    mod = mod.strip()
    if mod.startswith("src."):
        mod = mod[4:]
    parts = mod.split(".")
    if len(parts) < 2:
        return None
    file_rel = (Path("src") / Path(*parts)).with_suffix(".py").as_posix()
    pkg_rel = (Path("src") / Path(*parts) / "__init__.py").as_posix()
    if file_rel in bundle:
        return bundle[file_rel]
    if pkg_rel in bundle:
        return bundle[pkg_rel]
    fp = Path(file_rel)
    pp = Path(pkg_rel)
    if fp.exists():
        return fp.read_text(encoding="utf-8", errors="replace")
    if pp.exists():
        return pp.read_text(encoding="utf-8", errors="replace")
    return None


def _module_exports_from_source(source: str) -> set[str]:
    try:
        tree = ast.parse(normalize_newlines(source))
    except Exception:
        return set()
    exports: set[str] = set()
    explicit_all: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            exports.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                if isinstance(target, ast.Name):
                    exports.add(target.id)
                    if target.id == "__all__" and isinstance(value, (ast.List, ast.Tuple, ast.Set)):
                        for elt in value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                explicit_all.add(elt.value)
    return explicit_all or exports


def _class_methods_from_source(source: str, class_name: str) -> set[str]:
    try:
        tree = ast.parse(normalize_newlines(source))
    except Exception:
        return set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return set()


def _class_init_arity_from_source(source: str, class_name: str) -> Tuple[int, int | None] | None:
    try:
        tree = ast.parse(normalize_newlines(source))
    except Exception:
        return None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
                    total = len(getattr(item.args, "posonlyargs", [])) + len(item.args.args)
                    defaults = len(item.args.defaults)
                    min_args = max(0, total - defaults - 1)
                    max_args = None if item.args.vararg is not None else max(0, total - 1)
                    return min_args, max_args
    return None


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _is_simplenamespace_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and ((_call_name(node.func) or "").endswith("SimpleNamespace"))


def _protected_python_semantic_issues(bundle: Dict[str, str], task_text: str) -> List[str]:
    protected_modules = {
        "builder.orchestrator.runner",
        "builder.orchestrator.project_config",
        "builder.orchestrator.cli",
        "builder.orchestrator.backlog",
        "builder.orchestrator.execution_result",
    }
    runner_source = _module_source_for_name("builder.orchestrator.runner", bundle) or ""
    runner_methods = _class_methods_from_source(runner_source, "OrchestratorRunner")
    runner_ctor = _class_init_arity_from_source(runner_source, "OrchestratorRunner")
    config_requires_wrapper = "config.config" in runner_source
    issues: List[str] = []

    for rel, content in bundle.items():
        if not rel.endswith(".py"):
            continue
        try:
            tree = ast.parse(normalize_newlines(content), filename=rel)
        except Exception:
            continue
        imported_names: Dict[str, str] = {}
        var_types: Dict[str, str] = {}
        var_has_config: Dict[str, bool] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = (node.module or "").strip()
                if module.startswith("src."):
                    module = module[4:]
                if module in protected_modules:
                    source = _module_source_for_name(module, bundle)
                    exports = _module_exports_from_source(source or "") if source is not None else set()
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        imported_names[alias.asname or alias.name] = f"{module}.{alias.name}"
                        if source is not None and alias.name not in exports and _module_source_for_name(f"{module}.{alias.name}", bundle) is None:
                            issues.append(f"{rel}: imports missing symbol '{alias.name}' from '{module}'")

        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target = node.targets[0].id
                value = node.value
                if isinstance(value, ast.Call):
                    call_name = _call_name(value.func) or ""
                    resolved = imported_names.get(call_name, call_name)
                    if resolved.endswith("OrchestratorRunner") or call_name == "OrchestratorRunner":
                        var_types[target] = "OrchestratorRunner"
                        argc = len(value.args) + len([kw for kw in value.keywords if kw.arg is not None])
                        if runner_ctor is not None:
                            min_args, max_args = runner_ctor
                            if argc < min_args or (max_args is not None and argc > max_args):
                                req = str(min_args) if min_args == max_args else f"{min_args}-{max_args if max_args is not None else 'n'}"
                                issues.append(f"{rel}: OrchestratorRunner() is called with {argc} args but protected constructor requires {req}")
                        if config_requires_wrapper and value.args:
                            first = value.args[0]
                            bad_wrapper = False
                            if _is_simplenamespace_call(first):
                                bad_wrapper = not any((kw.arg == "config") for kw in first.keywords if kw.arg)
                            elif isinstance(first, ast.Name) and first.id in var_has_config:
                                bad_wrapper = not var_has_config[first.id]
                            if bad_wrapper:
                                issues.append(f"{rel}: OrchestratorRunner first arg must be ProjectConfig or object with .config")
                    elif _is_simplenamespace_call(value):
                        var_has_config[target] = any((kw.arg == "config") for kw in value.keywords if kw.arg)
                elif isinstance(value, ast.Name) and value.id in var_has_config:
                    var_has_config[target] = var_has_config[value.id]

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                obj = node.func.value.id
                attr = node.func.attr
                if var_types.get(obj) == "OrchestratorRunner" and runner_methods and attr not in runner_methods:
                    issues.append(f"{rel}: variable '{obj}' is an OrchestratorRunner; protected API has no method '{attr}'")
    deduped=[]
    seen=set()
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            deduped.append(issue)
    return deduped


def enforce_required_files(
    required: List[str],
    bundle: Dict[str, str],
    baseline: Dict[str, str] | None = None,
    *,
    require_material_update: bool = False,
    allow_unchanged_cli: bool = False,
) -> Tuple[bool, str]:
    missing = [rf for rf in required if rf not in bundle]
    if missing:
        return False, "Missing required deliverables (must be created/updated): " + ", ".join(missing)

    if require_material_update and baseline is not None:
        unchanged: List[str] = []
        for rf in required:
            if allow_unchanged_cli and rf == "src/builder/orchestrator/cli.py":
                continue
            if rf in baseline and baseline[rf] == bundle[rf]:
                unchanged.append(rf)
        if unchanged:
            return False, "Required deliverables were included but not materially updated: " + ", ".join(unchanged)

    return True, ""



def validate_static_bundle_contracts(bundle: Dict[str, str], task_text: str) -> Tuple[bool, str]:
    """Catch obvious structural and protected-API regressions before spending an iteration on ruff/pytest."""
    issues: List[str] = []
    directives = parse_task_contract_directives(task_text)

    runner_path = "src/builder/orchestrator/runner.py"
    runner = bundle.get(runner_path, "")
    if runner:
        defined_methods = set(RUNNER_METHOD_HEADER_RE.findall(runner))
        for method in parse_required_runner_methods(task_text):
            if method in {"select_next_task", "run_next_task", "execute_task", "process_execution_result", "simulate_backlog"} and method not in defined_methods:
                issues.append(f"`{runner_path}` is missing required method `{method}`.")
        lower_task = normalize_newlines(task_text).lower()
        if "processed_tasks" in lower_task and "simulate_backlog" in defined_methods:
            for key in ["processed_tasks", "stopped_reason", "final_status", "approval_required", "planned_actions"]:
                if key not in runner:
                    issues.append(f"`{runner_path}` appears to be missing simulation return key `{key}`.")

    project_config_path = "src/builder/orchestrator/project_config.py"
    project_config = bundle.get(project_config_path, "")
    if "@dataclass(frozen=True)" in project_config:
        issues.append(f"`{project_config_path}` uses frozen dataclasses, but the task requires mutable config objects.")

    cli_path = "src/builder/orchestrator/cli.py"
    cli = bundle.get(cli_path, "")
    if "default_task_runner" in cli:
        issues.append(f"`{cli_path}` invents `default_task_runner`, but the task requires no fallback command.")
    if "run_next_task(" in cli and "real_execution=" in cli:
        issues.append(f"`{cli_path}` calls `run_next_task(..., real_execution=...)`, but the task requires the legacy public signature.")

    for entry in directives.get("FORBID_CALLS", []):
        for forbidden in entry.split():
            for rel, content in bundle.items():
                if forbidden in content:
                    issues.append(f"`{rel}` violates FORBID_CALLS directive via `{forbidden}`.")

    issues.extend(_protected_python_semantic_issues(bundle, task_text))

    if issues:
        deduped=[]
        seen=set()
        for issue in issues:
            if issue not in seen:
                seen.add(issue)
                deduped.append(issue)
        return False, "Static bundle contract violations detected:\n" + "\n".join(f"- {x}" for x in deduped)
    return True, ""
def package_roots() -> List[str]:
    roots: List[str] = []
    src = Path("src")
    if src.exists():
        for child in sorted(src.iterdir()):
            if child.is_dir() and (child / "__init__.py").exists():
                roots.append(child.name)
    return roots


def import_regex_for_roots() -> re.Pattern[str]:
    roots = package_roots()
    if not roots:
        return re.compile(r"$^")
    escaped = "|".join(re.escape(r) for r in roots)
    return re.compile(
        rf"^\s*(?:from|import)\s+(({escaped})(?:\.[A-Za-z_][A-Za-z0-9_]*)+)",
        re.MULTILINE,
    )


def repo_map() -> str:
    roots = [Path("src"), Path("tests"), Path("agents"), Path("tasks")]
    out: List[str] = []
    for root in roots:
        if not root.exists():
            continue
        out.append(f"[{root.as_posix()}]")
        for path in sorted(root.rglob("*")):
            if path.is_dir():
                continue
            rel = path.as_posix()
            if "__pycache__" in rel or rel.endswith(".pyc"):
                continue
            out.append(rel)
        out.append("")
    return "\n".join(out).strip()


def relevant_context(required: List[str]) -> str:
    seen: set[str] = set()
    lines: List[str] = []

    # Only include agents dir and specific required files — skip bulk src/tests injection
    # to keep prompt size manageable as codebase grows
    candidates = [
        Path("agents"),
    ]

    for rf in required:
        p = Path(rf)
        if p.exists():
            candidates.append(p)
            if p.parent != Path("."):
                for sib in sorted(p.parent.glob("*.py")):
                    candidates.append(sib)

    for p in candidates:
        if not p.exists() or p.is_dir():
            continue
        rel = p.as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        snippet = "\n".join(content.splitlines()[:60])
        lines.append(f"### {rel}\n{snippet}\n")
    return "\n".join(lines).strip()


def module_exists(mod: str, bundle: Dict[str, str]) -> bool:
    parts = mod.split(".")
    if len(parts) < 2:
        return True
    file_candidate = Path("src") / Path(*parts).with_suffix(".py")
    pkg_candidate = Path("src") / Path(*parts) / "__init__.py"
    return (
        file_candidate.exists()
        or pkg_candidate.exists()
        or file_candidate.as_posix() in bundle
        or pkg_candidate.as_posix() in bundle
    )



def validate_imports(bundle: Dict[str, str]) -> Tuple[bool, str]:
    bad: List[str] = []
    import_re = import_regex_for_roots()
    for rel, content in bundle.items():
        for mod, _root in import_re.findall(content):
            if not module_exists(mod, bundle):
                bad.append(f"{rel}: imports missing module '{mod}'")
        if not rel.endswith(".py"):
            continue
        try:
            tree = ast.parse(normalize_newlines(content), filename=rel)
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            module = (node.module or "").strip()
            if module.startswith("src."):
                module = module[4:]
            if not module or not any(module == root or module.startswith(root + ".") for root in package_roots()):
                continue
            source = _module_source_for_name(module, bundle)
            if source is None:
                continue
            exports = _module_exports_from_source(source)
            for alias in node.names:
                if alias.name == "*":
                    continue
                if _module_source_for_name(f"{module}.{alias.name}", bundle) is not None:
                    continue
                if alias.name not in exports:
                    bad.append(f"{rel}: imports missing symbol '{alias.name}' from '{module}'")
    if not bad:
        return True, ""
    return False, "Invalid imports detected:\n" + "\n".join(sorted(set(bad)))
def missing_module_hints(import_msg: str) -> str:
    mods = re.findall(r"module '([^']+)'", import_msg)
    if not mods:
        return ""
    hints: List[str] = []
    for mod in sorted(set(mods)):
        parts = mod.split(".")
        if len(parts) < 2:
            continue
        file_path = (Path("src") / Path(*parts).with_suffix(".py")).as_posix()
        pkg_path = (Path("src") / Path(*parts) / "__init__.py").as_posix()
        hints.append(
            f"- Missing import target `{mod}`. Either change the import to an existing repo module, "
            f"or create `{file_path}` (or package `{pkg_path}`) in the same bundle."
        )
    return "\n".join(hints)


def parse_semantic_failures(details: str) -> str:
    lines: List[str] = []

    for path, lineno in sorted(set(RUFF_UNUSED_IMPORT_RE.findall(details))):
        lines.append(f"- Ruff reports unused imports in `{path}` line {lineno}. Remove the unused imports.")
    for path, lineno in sorted(set(RUFF_BOOL_COMPARE_RE.findall(details))):
        lines.append(
            f"- Ruff reports boolean equality comparisons in `{path}` line {lineno}. "
            "Use `assert x` or `assert not x` instead of `== True/False`."
        )
    for name in sorted(set(RUFF_UNDEFINED_NAME_RE.findall(details))):
        lines.append(f"- Ruff reports undefined name `{name}`. Define it or remove the reference.")

    for name in PYTEST_TEST_NAME_RE.findall(details)[:10]:
        lines.append(f"- Pytest failure: `{name}`")

    for path, lineno in sorted(set(PYTEST_TEST_FILE_RE.findall(details))):
        shown = path.replace("\\", "/")
        lines.append(
            f"- Modify implementation files to satisfy the failing expectation referenced by `{shown}` line {lineno}. "
            "Do not change tests unless the task explicitly requires it."
        )

    for actual, expected in PYTEST_EXACT_MISMATCH_RE.findall(details)[:10]:
        lines.append(
            f"- Exact mismatch: actual `{actual.strip()}` vs expected `{expected.strip()}`. "
            "Change the implementation so the expected value passes exactly."
        )

    for cls, attr in sorted(set(MISSING_ATTR_RE.findall(details))):
        if attr == "simulate_backlog":
            lines.append(
                f"- AttributeError detected: `{cls}` has no `{attr}`. Restore the required public method `{attr}` on the class."
            )
        else:
            lines.append(
                f"- AttributeError detected: `{cls}` has no `{attr}`. "
                "Guard the access with `getattr(..., None)` or skip the behavior when the field is not configured."
            )

    for mod in sorted(set(MODULE_NOT_FOUND_RE.findall(details))):
        lines.append(f"- Missing module `{mod}`. Change the import or create the module in the bundle.")

    for name in sorted(set(NAME_ERROR_RE.findall(details))):
        lines.append(f"- NameError for `{name}`. Define the name before using it.")

    for key in sorted(set(KEY_ERROR_RE.findall(details))):
        lines.append(f"- KeyError for `{key}`. Preserve expected response keys and dictionary fields.")

    if WIN_ECHO_RE.search(details):
        lines.append(
            "- A Windows subprocess command failed to resolve. Do not assume `echo` is a standalone executable on Windows. "
            "Prefer `sys.executable` + `-c` for cross-platform tests, or guard subprocess execution on the legacy path."
        )

    seen = set()
    out: List[str] = []
    for line in lines:
        if line not in seen:
            out.append(line)
            seen.add(line)
    return "\n".join(out)


def bundle_similarity(a: Dict[str, str] | None, b: Dict[str, str] | None) -> float:
    if not a or not b:
        return 0.0
    left = "\n".join(f"FILE:{k}\n{a[k]}" for k in sorted(a))
    right = "\n".join(f"FILE:{k}\n{b[k]}" for k in sorted(b))
    return difflib.SequenceMatcher(None, left, right).ratio()


def run_checks() -> Tuple[bool, str]:
    details: List[str] = []

    # Let the model auto-fix simple ruff issues first.
    capture_result([sys.executable, "-m", "ruff", "check", ".", "--fix"])

    ruff = capture_result([sys.executable, "-m", "ruff", "check", "."])
    if ruff.returncode != 0:
        details.append("## ruff\n" + (ruff.stdout or "") + (ruff.stderr or ""))

    pytest = capture_result([sys.executable, "-m", "pytest", "-q"])
    if pytest.returncode != 0:
        details.append("## pytest\n" + (pytest.stdout or "") + (pytest.stderr or ""))

    if details:
        return False, "\n".join(details).strip()
    return True, ""


def load_system_prompt() -> str:
    candidates = [
        Path("agents/prompts/system.md"),
        Path("system.md"),
        Path("agents/prompts/system_prompt.md"),
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
    return "You are an engineering agent. Output ONLY a valid file bundle."


def chat_openai(messages: List[dict], model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment.")
    from openai import APITimeoutError, OpenAI  # type: ignore

    timeout_s = _float_env("TRADINGBOT_OPENAI_TIMEOUT", 900.0)
    max_attempts = max(1, _int_env("TRADINGBOT_OPENAI_RETRIES", 2))
    client = OpenAI(api_key=api_key, timeout=timeout_s)

    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.chat.completions.create(model=model, messages=messages)
            content = resp.choices[0].message.content
            if isinstance(content, str):
                return content.strip()
            return ""
        except APITimeoutError as exc:
            last_err = exc
            if attempt == max_attempts:
                raise
            wait_s = min(5 * attempt, 15)
            print(f"OpenAI request timed out on attempt {attempt}/{max_attempts}; retrying in {wait_s}s...", file=sys.stderr)
            time.sleep(wait_s)
    if last_err is not None:
        raise last_err
    return ""


def chat_anthropic(messages: List[dict], model: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY in environment.")
    import anthropic  # type: ignore

    timeout_s = _float_env("TRADINGBOT_ANTHROPIC_TIMEOUT", 900.0)
    max_attempts = max(1, _int_env("TRADINGBOT_ANTHROPIC_RETRIES", 2))
    client = anthropic.Anthropic(api_key=api_key, timeout=timeout_s)
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    user_msgs = [m for m in messages if m["role"] != "system"]

    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.messages.create(model=model, max_tokens=12000, system=system, messages=user_msgs)
            return (resp.content[0].text or "").strip()
        except Exception as exc:
            last_err = exc
            if attempt == max_attempts or "timeout" not in str(exc).lower():
                raise
            wait_s = min(5 * attempt, 15)
            print(f"Anthropic request timed out on attempt {attempt}/{max_attempts}; retrying in {wait_s}s...", file=sys.stderr)
            time.sleep(wait_s)
    if last_err is not None:
        raise last_err
    return ""


def chat(messages: List[dict], model: str, provider: str | None = None) -> str:
    chosen = (provider or default_provider()).strip().lower()
    if chosen == "openai":
        return chat_openai(messages, model)
    if chosen == "anthropic":
        return chat_anthropic(messages, model)
    raise RuntimeError(f"Unsupported provider: {chosen}")


def build_messages(
    task_text: str,
    required: List[str],
    extra_directives: str = "",
    virtual_context: Dict[str, str] | None = None,
) -> List[dict]:
    extra: List[str] = []

    if required:
        extra.append("## Required deliverables (must be satisfied)")
        extra.extend(f"- {p}" for p in required)
        extra.append("")
        extra.append("## Exact FILE headers that MUST appear")
        for p in required:
            extra.append(f"FILE: {p}")
        extra.append("")
        extra.append("## Output requirements")
        extra.append("You MUST emit FILE blocks for every required deliverable path listed above.")
        extra.append("Every FILE block must be closed by END_FILE before the next FILE header.")
        extra.append("If a deliverable is an existing file, materially update it in the bundle.")
        extra.append("Do not omit test files named in the task.")
        extra.append("Do not substitute similar or nested alternative paths.")
        extra.append("")

    extra.append("## Update discipline")
    extra.append("When updating an existing file, preserve the current architecture and surrounding code unless the task explicitly requires a rewrite.")
    extra.append("Do not replace large existing files with miniature standalone versions or toy implementations.")
    extra.append("")
    extra.append("## Relevant file context")
    extra.append(relevant_context(required) or "(none)")

    if virtual_context:
        extra.append("")
        extra.append("## Effective protected-file context (authoritative for this iteration)")
        extra.append(
            "These files are handled by the harness outside the normal bundle. "
            "Use their exact content below when generating dependent files like tests."
        )
        for rel, content in virtual_context.items():
            extra.append(f"FILE: {rel}")
            extra.append(content.rstrip("\n"))
            extra.append("END_FILE")

    extra.append("")
    extra.append("## Repository map")
    extra.append(repo_map())

    if extra_directives.strip():
        extra.append("")
        extra.append("## Iteration-specific directives")
        extra.append(extra_directives.strip())

    user_task = task_text.rstrip() + "\n\n" + "\n".join(extra).rstrip() + "\n"
    return [
        {"role": "system", "content": load_system_prompt().strip()},
        {"role": "user", "content": user_task},
    ]


def request_and_parse_bundle(messages: List[dict], model: str, provider: str, last_output_path: Path) -> Dict[str, str]:
    out = chat(messages, model=model, provider=provider)
    last_output_path.write_text(out + "\n", encoding="utf-8", newline="\n")

    try:
        return parse_file_bundle(out)
    except Exception as e:
        reminder = (
            "Your previous response was INVALID.\n"
            "You MUST output ONLY a valid file bundle using literal lines starting with 'FILE: '.\n"
            "Do NOT use commented headers like '# FILE:'.\n"
            "Every FILE block MUST be terminated by a literal END_FILE line before the next FILE header.\n"
            "There must be an END_FILE before any later FILE header.\n"
            "Do not open a new FILE block until the previous FILE block is closed.\n\n"
            "Required structure:\n"
            "BEGIN_FILE_BUNDLE\n"
            "FILE: path/to/file.ext\n"
            "<full file contents>\n"
            "END_FILE\n"
            "FILE: another/path.py\n"
            "<full file contents>\n"
            "END_FILE\n"
            "END_FILE_BUNDLE\n\n"
            f"Parser error: {e}"
        )
        out2 = chat(messages + [{"role": "user", "content": reminder}], model=model, provider=provider)
        last_output_path.write_text(out2 + "\n", encoding="utf-8", newline="\n")
        try:
            return parse_file_bundle(out2)
        except Exception as e2:
            raise FileBundleError(f"Model returned malformed file bundle after retry: {e2}") from e2


def main() -> int:
    _load_dotenv_if_available()

    ap = argparse.ArgumentParser()
    ap.add_argument("task", help="Path to task markdown, e.g. tasks/008_risk_gate.md")
    ap.add_argument("--push", action="store_true", help="Commit + push the resulting branch")
    ap.add_argument("--provider", default=default_provider(), choices=["openai", "anthropic"])
    ap.add_argument("--model", default=default_model_for_provider(default_provider()))
    ap.add_argument("--max-iters", type=int, default=4)
    ap.add_argument("--policy-block-limit", type=int, default=_int_env("TRADINGBOT_POLICY_BLOCK_LIMIT", 2))
    args = ap.parse_args()
    if not hasattr(args, "provider"):
        args.provider = default_provider()
    if not hasattr(args, "model") or not args.model:
        args.model = default_model_for_provider(args.provider)

    task_path = Path(args.task)
    if not task_path.exists():
        raise SystemExit(f"Task file not found: {task_path}")

    ensure_clean_worktree()

    task_text = task_path.read_text(encoding="utf-8", errors="replace")
    required = parse_required_files(task_text)
    require_material_update = task_requires_material_update(task_text)
    allow_unchanged_cli = task_allows_unchanged_cli(task_text)
    harness_policies = parse_harness_file_policies(task_text)
    baseline_paths = sorted(set(required) | set(harness_policies.keys()))
    protected_targets = _extract_protected_method_targets(task_text)
    protected_method_paths = {str(t["path"]) for t in protected_targets}

    branch = f"agent-{task_path.stem}"
    print(f"Current branch: {capture(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])}")
    print(f"Creating branch: {branch}")
    print(f"Using provider: {args.provider}")
    print(f"Using model: {args.model}")
    ensure_branch(branch)

    last_output_path = Path("_last_agent_model_output.txt")
    last_bundle_path = Path("_last_agent_file_bundle.txt")

    prev_files: Dict[str, str] | None = None
    extra_directives = ""
    violation_counts: Dict[str, int] = {}

    stable_baseline = existing_file_contents(baseline_paths)

    for it in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {it}/{args.max_iters} ===")
        baseline = existing_file_contents(baseline_paths)
        for protected_path in protected_method_paths:
            if protected_path in stable_baseline:
                baseline[protected_path] = stable_baseline[protected_path]
            else:
                baseline.pop(protected_path, None)
        bundle_required = [p for p in required if p not in protected_method_paths]

        files: Dict[str, str] = {}
        try:
            for target in protected_targets:
                target_path = str(target["path"])
                mode = str(target["mode"])
                method_name = str(target["method_name"])
                baseline_content = baseline.get(target_path)
                if baseline_content is None:
                    raise FileBundleError(
                        f"Protected method target `{target_path}` has no baseline content."
                    )
                anchor = str(target.get("anchor", "")) if mode == "append" else ""
                insertion_messages = build_method_insertion_messages(
                    task_text,
                    target_path,
                    method_name,
                    baseline_content,
                    mode,
                    extra_directives,
                    anchor=anchor,
                )
                method_text = request_and_parse_method_insertion(
                    insertion_messages,
                    args.model,
                    args.provider,
                    last_output_path,
                    target_path,
                    method_name,
                )
                if mode == "append":
                    files[target_path] = apply_method_insertion(
                        baseline_content,
                        anchor,
                        method_name,
                        method_text,
                    )
                else:
                    files[target_path] = apply_method_replacement(
                        baseline_content,
                        method_name,
                        method_text,
                    )

            if bundle_required:
                non_protected_directives = extra_directives
                if protected_method_paths:
                    suffix = (
                        "Do not emit protected method-edit files in the normal file bundle; "
                        "they are handled separately by protected method mode. If you include them anyway, "
                        "they will be ignored."
                    )
                    non_protected_directives = (
                        (extra_directives.rstrip() + "\n\n") if extra_directives.strip() else ""
                    ) + suffix
                virtual_context = {p: files[p] for p in sorted(protected_method_paths) if p in files}
                messages = build_messages(
                    task_text,
                    bundle_required,
                    non_protected_directives,
                    virtual_context=virtual_context,
                )
                generated = request_and_parse_bundle(
                    messages, args.model, args.provider, last_output_path
                )
                overlap = sorted(set(generated) & protected_method_paths)
                if overlap:
                    print(
                        "ℹ️ Ignoring protected method-edit files emitted in normal bundle: "
                        + ", ".join(overlap)
                    )
                    task_text = _append_task_feedback(
                        task_text,
                        "Do not emit protected method-edit files in the normal file bundle. "
                        "Only emit non-protected deliverables there.",
                    )
                    for p in overlap:
                        generated.pop(p, None)
                files.update(generated)
            elif not files:
                virtual_context = {p: files[p] for p in sorted(protected_method_paths) if p in files}
                messages = build_messages(
                    task_text,
                    required,
                    extra_directives,
                    virtual_context=virtual_context,
                )
                files = request_and_parse_bundle(
                    messages, args.model, args.provider, last_output_path
                )
        except FileBundleError as e:
            print(f"❌ {e}")
            print(f"Model output saved to: {last_output_path}")
            print(f"Parsed file bundle saved to: {last_bundle_path}")
            return 1

        pretty: List[str] = [FILE_BUNDLE_BEGIN]
        for p, c in files.items():
            pretty.append(f"FILE: {p}")
            pretty.append(c.rstrip("\n"))
            pretty.append(FILE_END)
        pretty.append(FILE_BUNDLE_END)
        last_bundle_path.write_text("\n".join(pretty) + "\n", encoding="utf-8", newline="\n")

        ok_syntax, syntax_msg = validate_python_syntax(files)
        if not ok_syntax:
            print(f"❌ {syntax_msg}")
            task_text = _append_task_feedback(task_text, syntax_msg)
            if _repeat_limit_exceeded(violation_counts, "python_syntax", args.policy_block_limit):
                print("\n❌ Stopping early: repeated Python syntax failures. Recommended action: manual_patch")
                print("Model output saved to: _last_agent_model_output.txt")
                print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
                return 1
            prev_files = files
            continue

        ok_req, req_msg = enforce_required_files(
            required,
            files,
            baseline,
            require_material_update=require_material_update,
            allow_unchanged_cli=allow_unchanged_cli,
        )
        if not ok_req:
            print(f"❌ {req_msg}")
            task_text = _append_task_feedback(task_text, req_msg)
            if _repeat_limit_exceeded(violation_counts, "deliverables", args.policy_block_limit):
                print("\n❌ Stopping early: repeated deliverable violations. Recommended action: manual_patch")
                print("Model output saved to: _last_agent_model_output.txt")
                print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
                return 1
            prev_files = files
            continue

        ok_policy, policy_msg = enforce_harness_file_policies(task_text, files, baseline)
        if not ok_policy:
            print(f"❌ {policy_msg}")
            task_text = _append_task_feedback(task_text, policy_msg)
            if _repeat_limit_exceeded(violation_counts, "protected_file_policy", args.policy_block_limit):
                print("\n❌ Stopping early: repeated protected-file policy violations. Recommended action: manual_patch")
                print("Model output saved to: _last_agent_model_output.txt")
                print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
                return 1
            prev_files = files
            continue

        ok_static, static_msg = validate_static_bundle_contracts(files, task_text)
        if not ok_static:
            print(f"❌ {static_msg}")
            task_text = _append_task_feedback(task_text, static_msg)
            if _repeat_limit_exceeded(violation_counts, "static_contracts", args.policy_block_limit):
                print("\n❌ Stopping early: repeated static contract violations. Recommended action: manual_patch")
                print("Model output saved to: _last_agent_model_output.txt")
                print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
                return 1
            prev_files = files
            continue

        ok_imports, import_msg = validate_imports(files)
        if not ok_imports:
            print(f"❌ {import_msg}")
            task_text = _append_task_feedback(task_text, import_msg + "\n" + missing_module_hints(import_msg))
            if _repeat_limit_exceeded(violation_counts, "imports", args.policy_block_limit):
                print("\n❌ Stopping early: repeated import validation failures. Recommended action: manual_patch")
                print("Model output saved to: _last_agent_model_output.txt")
                print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
                return 1
            prev_files = files
            continue

        pre_write_snapshot = snapshot_file_contents(list(files.keys()))
        write_files(files)
        violation_counts.clear()

        ok, details = run_checks()
        if ok:
            print("✅ Green.")
            if args.push:
                run(["git", "add", "-A"], check=True)
                staged = capture(["git", "diff", "--cached", "--name-only"])
                if not staged.strip():
                    print("✅ Green. No changes to commit/push.")
                    return 0
                run(["git", "commit", "-m", f"{task_path.stem}: apply agent changes"], check=True)
                run(["git", "push", "-u", "origin", branch], check=True)
                print(f"Pushed branch: {branch}")
                print("Create a PR on GitHub for this branch (repo rules require PR).")
            return 0

        restore_file_snapshot(pre_write_snapshot)

        print("❌ Checks failed after applying changes:")
        print(details)

        semantic_hints = parse_semantic_failures(details)
        task_text = (
            task_text.rstrip()
            + "\n\n# Last run failures\n"
            + details
            + "\n\nIMPORTANT: Fix the reported failures exactly. "
              "Modify implementation files to satisfy failing tests. "
              "Do not change tests unless the task explicitly requires it. "
              "Use exact expected values from pytest output as the source of truth.\n"
        )
        if semantic_hints:
            task_text += "\n# Failure analysis hints\n" + semantic_hints + "\n"

        if prev_files is not None:
            sim = bundle_similarity(prev_files, files)
            if sim > 0.98:
                task_text += (
                    "\n# Escalation\n"
                    "Your latest bundle is materially unchanged from the previous attempt, but tests still fail. "
                    "You must make a real implementation change in the most likely source file causing the failure. "
                    "Do not resubmit the same logic. Prefer changing the implementation rather than the tests. "
                    "If helper methods exist, update them consistently instead of patching only one call site. "
                    "If the failure mentions an optional config field or invalid file path, remove the call or guard it before invoking the helper. "
                    "Before writing code, statically inspect the failing symbols, exact mismatches, and task constraints. "
                    "Patch the smallest implementation surface that satisfies the exact failing assertions while preserving public APIs.\n"
                )

        prev_files = files

    print("\n❌ Failed to reach green within max iterations.")
    print("Model output saved to: _last_agent_model_output.txt")
    print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())