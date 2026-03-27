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
import random
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

FILE_BUNDLE_BEGIN = "BEGIN_FILE_BUNDLE"
FILE_BUNDLE_END = "END_FILE_BUNDLE"
FILE_BEGIN_PREFIX = "FILE:"
FILE_END = "END_FILE"

DELIVERABLE_PATH_RE = re.compile(r"`([^`]+\.[A-Za-z0-9_]+)`")
FILE_HEADER_RE = re.compile(r"^\s*(?:#\s*)?FILE:\s*(.+?)\s*$")
BUNDLE_FILE_HEADER_RE = re.compile(r"^FILE:\s*(.+?)\s*$")
RUNNER_METHOD_HEADER_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)
TASK_FILE_POLICY_RE = re.compile(r"^\s*-\s*FILE:\s*(?P<path>\S+)(?P<rest>.*)$")
TASK_FILE_ATTR_RE = re.compile(r'([A-Z_]+)=(".*?"|\'.*?\'|[^\s]+)')
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

RUNTIME_ARTIFACT_NAMES = (
    "last_output.txt",
    "_last_agent_model_output.txt",
    "_last_agent_file_bundle.txt",
)


class FileBundleError(ValueError):
    pass


def _ensure_repo_root_on_sys_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


_ensure_repo_root_on_sys_path()


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

    def __repr__(self) -> str:
        return (
            "NormalizedLLMResponse("
            f"text={self.text!r}, stop_reason={self.stop_reason!r}, "
            f"usage_input_tokens={self.usage_input_tokens!r}, "
            f"usage_output_tokens={self.usage_output_tokens!r}, "
            f"request_id={self.request_id!r})"
        )


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv()


def _default_provider_impl() -> str:
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
        return "gpt-5.4"
    return "claude-sonnet-4-6"


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
    try:
        from agents.lib.bundle_parser import parse_file_bundle as _parse_file_bundle  # type: ignore
    except Exception:
        _parse_file_bundle = None  # type: ignore[assignment]

    if _parse_file_bundle is not None:
        return _parse_file_bundle(
            text=text,
            normalize_newlines=normalize_newlines,
            file_bundle_begin=FILE_BUNDLE_BEGIN,
            file_bundle_end=FILE_BUNDLE_END,
            file_header_re=FILE_HEADER_RE,
            file_end=FILE_END,
            error_cls=FileBundleError,
        )

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


def _normalize_method_token(token: str) -> str:
    token = token.strip().strip("`").strip('"').strip("'")
    if token.startswith("def "):
        token = token[4:]
    if "(" in token:
        token = token.split("(", 1)[0]
    if ":" in token:
        token = token.split(":", 1)[0]
    return token.strip()


def _normalize_policy_path(token: str) -> str:
    token = token.strip().strip("`").strip('"').strip("'")
    return token.replace("\\", "/").strip()


def _parse_task_file_attrs(rest: str) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    text = (rest or "").strip()
    if not text:
        return attrs

    pos = 0
    key_re = re.compile(r"[A-Z][A-Z0-9_]*")

    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text):
            break

        key_match = key_re.match(text, pos)
        if not key_match:
            pos += 1
            continue

        key_end = key_match.end()
        if key_end >= len(text) or text[key_end] != "=":
            pos = key_end
            continue

        key = key_match.group(0)
        value_start = key_end + 1
        pos = value_start

        if pos < len(text) and text[pos] in {'"', "'"}:
            quote = text[pos]
            pos += 1
            value_chars: List[str] = []
            while pos < len(text):
                ch = text[pos]
                if ch == "\\" and pos + 1 < len(text):
                    value_chars.append(text[pos + 1])
                    pos += 2
                    continue
                if ch == quote:
                    pos += 1
                    break
                value_chars.append(ch)
                pos += 1
            attrs[key] = "".join(value_chars)
            continue

        next_key = re.search(r"\s+([A-Z][A-Z0-9_]*)=", text[pos:])
        if next_key:
            value_end = pos + next_key.start()
            value = text[value_start:value_end].strip()
            pos = value_end
        else:
            value = text[value_start:].strip()
            pos = len(text)
        attrs[key] = value

    return attrs

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
    try:
        from agents.lib.protected_file_policy import parse_harness_file_policies as _parse_harness_file_policies  # type: ignore
    except Exception:
        _parse_harness_file_policies = None  # type: ignore[assignment]

    if _parse_harness_file_policies is not None:
        return _parse_harness_file_policies(
            task_text=task_text,
            iter_markdown_sections=_iter_markdown_sections,
            task_file_policy_re=TASK_FILE_POLICY_RE,
            parse_task_file_attrs=_parse_task_file_attrs,
            normalize_anchor_token=_normalize_anchor_token,
            normalize_method_token=_normalize_method_token,
        )

    policies: Dict[str, Dict[str, object]] = {}
    allowed_section_names = {
        "deliverables",
        "harness policy",
        "machine-readable contract directives",
    }

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
                normalized_path = _normalize_policy_path(path)
                normalized_rule = rule.strip()
                if normalized_path and normalized_rule:
                    entry = policies.setdefault(normalized_path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(normalized_rule)
                continue

            if not parse_file_directives:
                continue

            m = TASK_FILE_POLICY_RE.match(line)
            if not m:
                continue
            if "MODE=" not in line:
                continue
            path = _normalize_policy_path(m.group("path"))
            attrs = _parse_task_file_attrs((m.group("rest") or "").strip())
            mode = attrs.get("MODE", "").strip().upper()
            if not path or not mode:
                continue
            if mode == "PROTECTED_FORBID":
                entry = policies.setdefault(path, {"rules": []})
                rules = entry.setdefault("rules", [])
                if isinstance(rules, list):
                    rules.append("forbid")
            elif mode == "EXACT_COPY":
                entry = policies.setdefault(path, {"rules": []})
                rules = entry.setdefault("rules", [])
                if isinstance(rules, list):
                    rules.append("exact_copy")
            elif mode == "EXACT_COPY_PLUS_APPEND_METHOD":
                anchor = attrs.get("ANCHOR_BEFORE", "").strip()
                if anchor:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"append_before:{_normalize_anchor_token(anchor)}")
                allow_method = _normalize_method_token(attrs.get("ALLOW_NEW_METHOD", "").strip())
                if allow_method:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"allow_methods:{allow_method}")
                max_changed = attrs.get("MAX_CHANGED_LINES", "").strip()
                if max_changed:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"max_changed_lines:{max_changed}")
            elif mode == "EXACT_COPY_PLUS_REPLACE_METHOD":
                replace_method = _normalize_method_token(
                    attrs.get("TARGET_METHOD", "").strip()
                    or attrs.get("REPLACE_METHOD", "").strip()
                    or attrs.get("ALLOW_EXISTING_METHOD", "").strip()
                )
                if replace_method:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"replace_method:{replace_method}")
                        rules.append(f"allow_methods:{replace_method}")
                max_changed = attrs.get("MAX_CHANGED_LINES", "").strip()
                if max_changed:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"max_changed_lines:{max_changed}")
            elif mode == "METHOD_ADD_ONLY":
                allow_method = _normalize_method_token(attrs.get("ALLOW_NEW_METHOD", "").strip())
                if allow_method:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"allow_methods:{allow_method}")
                max_changed = attrs.get("MAX_CHANGED_LINES", "").strip()
                if max_changed:
                    entry = policies.setdefault(path, {"rules": []})
                    rules = entry.setdefault("rules", [])
                    if isinstance(rules, list):
                        rules.append(f"max_changed_lines:{max_changed}")
    return policies
def _extract_protected_method_targets(task_text: str) -> List[Dict[str, object]]:
    try:
        from agents.lib.protected_file_policy import extract_protected_method_targets as _extract_targets  # type: ignore
    except Exception:
        _extract_targets = None  # type: ignore[assignment]

    if _extract_targets is not None:
        return _extract_targets(
            task_text=task_text,
            iter_markdown_sections=_iter_markdown_sections,
            task_file_policy_re=TASK_FILE_POLICY_RE,
            parse_task_file_attrs=_parse_task_file_attrs,
            normalize_anchor_token=_normalize_anchor_token,
            normalize_method_token=_normalize_method_token,
        )

    targets: List[Dict[str, object]] = []
    allowed_section_names = {
        "deliverables",
        "harness policy",
        "machine-readable contract directives",
    }

    for section_name, section_lines in _iter_markdown_sections(task_text):
        if section_name not in allowed_section_names:
            continue

        for raw_line in section_lines:
            line = raw_line.strip()
            if not line:
                continue

            m = TASK_FILE_POLICY_RE.match(line)
            if not m or "MODE=" not in line:
                continue

            path = _normalize_policy_path(m.group("path"))
            attrs = _parse_task_file_attrs((m.group("rest") or "").strip())
            mode = attrs.get("MODE", "").strip().upper()
            if not path or not mode:
                continue

            max_changed_lines = None
            raw_limit = attrs.get("MAX_CHANGED_LINES", "").strip()
            if raw_limit:
                try:
                    max_changed_lines = int(raw_limit)
                except ValueError:
                    max_changed_lines = None

            if mode == "EXACT_COPY_PLUS_REPLACE_METHOD":
                method_name = _normalize_method_token(
                    attrs.get("TARGET_METHOD", "").strip()
                    or attrs.get("REPLACE_METHOD", "").strip()
                    or attrs.get("ALLOW_EXISTING_METHOD", "").strip()
                )
                if method_name:
                    targets.append(
                        {
                            "path": path,
                            "mode": "replace",
                            "method_name": method_name,
                            "max_changed_lines": max_changed_lines,
                        }
                    )
            elif mode == "EXACT_COPY_PLUS_APPEND_METHOD":
                method_name = _normalize_method_token(attrs.get("ALLOW_NEW_METHOD", "").strip())
                anchor = attrs.get("ANCHOR_BEFORE", "").strip()
                if method_name and anchor:
                    targets.append(
                        {
                            "path": path,
                            "mode": "append",
                            "anchor": _normalize_anchor_token(anchor),
                            "method_name": method_name,
                            "max_changed_lines": max_changed_lines,
                        }
                    )

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


def _normalize_policy_tail_for_compare(content: str, anchor: str) -> str:
    normalized = normalize_newlines(content)
    lines = normalized.split("\n")
    anchor_idx = None
    for idx, line in enumerate(lines):
        if anchor in line:
            anchor_idx = idx
            break
    if anchor_idx is None:
        return normalized
    tail = lines[anchor_idx:]
    while tail and not tail[-1].strip():
        tail.pop()
    return "\n".join(line.rstrip() for line in tail)

def _anchor_context_excerpt(content: str, anchor: str, *, radius: int = 4) -> str:
    normalized = normalize_newlines(content)
    lines = normalized.splitlines()
    for idx, line in enumerate(lines):
        if anchor in line:
            start = max(0, idx - radius)
            end = min(len(lines), idx + radius + 1)
            excerpt_lines: List[str] = []
            for line_no in range(start, end):
                marker = ">>" if line_no == idx else "  "
                excerpt_lines.append(f"{marker} {line_no + 1:04d}: {lines[line_no]}")
            return "\n".join(excerpt_lines)
    return f"(anchor `{anchor}` not found in content excerpt generation)"


def _protected_overlap_issue(forbidden_paths: List[str], bundle: Dict[str, str]) -> str:
    overlap = sorted(set(bundle) & set(forbidden_paths))
    if not overlap:
        return ""
    listed = ", ".join(overlap)
    return (
        "Normal file bundle illegally included protected path(s): "
        f"{listed}. These files are handled separately by protected method mode and MUST NOT appear as FILE blocks in the normal bundle."
    )


def _top_level_function_names(source: str) -> set[str]:
    try:
        tree = ast.parse(normalize_newlines(source))
    except Exception:
        return set()
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def enforce_harness_file_policies(task_text: str, bundle: Dict[str, str], baseline: Dict[str, str]) -> Tuple[bool, str]:
    issues: List[str] = []
    policies = parse_harness_file_policies(task_text)
    for path, config in policies.items():
        rules = config.get("rules", [])
        if not isinstance(rules, list):
            continue
        proposed = bundle.get(path)
        original = baseline.get(path)

        allowed_methods: set[str] = set()
        for rule in rules:
            if isinstance(rule, str) and rule.startswith("allow_methods:"):
                allowed_methods.update(
                    name.strip()
                    for name in rule.split("allow_methods:", 1)[1].split(",")
                    if name.strip()
                )

        if allowed_methods and proposed is not None and original is not None:
            original_methods = _top_level_function_names(original)
            proposed_methods = _top_level_function_names(proposed)
            removed = original_methods - proposed_methods
            added = proposed_methods - original_methods
            disallowed_added = sorted(name for name in added if name not in allowed_methods)
            if removed:
                issues.append(
                    f"`{path}` removed existing methods under `allow_methods` policy: {', '.join(sorted(removed))}."
                )
            if disallowed_added:
                issues.append(
                    f"`{path}` added disallowed methods under `allow_methods` policy: {', '.join(disallowed_added)}."
                )

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
                    issues.append(
                        f"`{path}` changed content at or after protected anchor `{anchor}`. Only additive insertion before the anchor is allowed.\n"
                        f"Baseline anchor excerpt:\n{_anchor_context_excerpt(original, anchor)}\n"
                        f"Proposed anchor excerpt:\n{_anchor_context_excerpt(proposed, anchor)}"
                    )
                    continue
                original_before, _original_after = original.split(anchor, 1)
                proposed_before, _proposed_after = proposed.split(anchor, 1)
                original_tail = _normalize_policy_tail_for_compare(original, anchor)
                proposed_tail = _normalize_policy_tail_for_compare(proposed, anchor)
                if proposed_tail != original_tail:
                    issues.append(
                        f"`{path}` changed content at or after protected anchor `{anchor}`. Only additive insertion before the anchor is allowed.\n"
                        f"Baseline anchor excerpt:\n{_anchor_context_excerpt(original, anchor)}\n"
                        f"Proposed anchor excerpt:\n{_anchor_context_excerpt(proposed, anchor)}"
                    )
                    continue
                if normalize_newlines(proposed_before) == normalize_newlines(original_before):
                    issues.append(
                        f"`{path}` is protected by `append_before:{anchor}`, but no additive insertion before the anchor was detected.\n"
                        f"Baseline anchor excerpt:\n{_anchor_context_excerpt(original, anchor)}\n"
                        f"Proposed anchor excerpt:\n{_anchor_context_excerpt(proposed, anchor)}"
                    )
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
    method_text = _validate_single_method_text(
        method_text,
        method_name,
        context=f"Method insertion payload for `{method_name}`",
    )
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
    method_text = _validate_single_method_text(
        method_text,
        method_name,
        context=f"Method replacement payload for `{method_name}`",
    )
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
        if cur_indent <= method_indent:
            end_idx = idx
            break
    return "\n".join(lines[start_idx:end_idx]).rstrip("\n") + "\n"


def _validate_single_method_text(method_text: str, expected_method_name: str, *, context: str) -> str:
    method_text = normalize_newlines(method_text).rstrip("\n") + "\n"
    try:
        tree = ast.parse(method_text)
    except SyntaxError as exc:
        raise FileBundleError(
            f"{context}: extracted method body has Python syntax error at line {exc.lineno or 0}: {exc.msg or 'invalid syntax'}."
        ) from exc

    top_level_defs = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if top_level_defs != [expected_method_name]:
        raise FileBundleError(
            f"{context}: expected exactly one top-level method `{expected_method_name}`; got {top_level_defs or 'none'}. "
            "Do not define nested or additional helper defs inside the method payload; inline helper logic instead."
        )
    if len(tree.body) != 1:
        raise FileBundleError(
            f"{context}: method payload must contain exactly one top-level function definition and no trailing top-level statements."
        )
    return method_text


def parse_method_insertion_bundle(text: str, expected_path: str, expected_method_name: str) -> str:
    try:
        from agents.lib.bundle_parser import parse_method_insertion_bundle as _parse_method_insertion_bundle  # type: ignore
    except Exception:
        _parse_method_insertion_bundle = None  # type: ignore[assignment]

    if _parse_method_insertion_bundle is not None:
        return _parse_method_insertion_bundle(
            text=text,
            expected_path=expected_path,
            expected_method_name=expected_method_name,
            normalize_newlines=normalize_newlines,
            method_insertion_begin=METHOD_INSERTION_BEGIN,
            method_insertion_end=METHOD_INSERTION_END,
            method_block_begin=METHOD_BLOCK_BEGIN,
            method_block_end=METHOD_BLOCK_END,
            file_bundle_begin=FILE_BUNDLE_BEGIN,
            file_header_re=FILE_HEADER_RE,
            file_end=FILE_END,
            validate_single_method_text=_validate_single_method_text,
            error_cls=FileBundleError,
        )

    expected_path = str(expected_path)
    expected_method_name = str(expected_method_name)
    text = normalize_newlines(text)
    lines = text.split("\n")

    if METHOD_INSERTION_BEGIN not in text:
        if FILE_BUNDLE_BEGIN in text:
            raise FileBundleError(
                "Method insertion response used BEGIN_FILE_BUNDLE. Protected-file method mode requires BEGIN_METHOD_INSERTION / END_METHOD_INSERTION."
            )
        raise FileBundleError("Method insertion response did not include BEGIN_METHOD_INSERTION / END_METHOD_INSERTION markers.")

    begin_idx = next((i for i, line in enumerate(lines) if line.strip() == METHOD_INSERTION_BEGIN), None)
    if begin_idx is None:
        raise FileBundleError("Missing BEGIN_METHOD_INSERTION in method insertion bundle.")
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
            if target_file != expected_path:
                raise FileBundleError(f"Method insertion target file mismatch: expected {expected_path}, got {target_file}.")
            if method_name != expected_method_name:
                raise FileBundleError(f"Method insertion method mismatch: expected {expected_method_name}, got {method_name}.")
            return _validate_single_method_text("\n".join(buf).rstrip("\n") + "\n", expected_method_name, context="Method insertion bundle")
        i += 1

    raise FileBundleError("Method insertion response did not include BEGIN_METHOD / END_METHOD block.")
def load_method_insertion_system_prompt() -> str:
    base = load_system_prompt().strip()
    override = (
        "PROTECTED-FILE METHOD MODE OVERRIDE:\n"
        "When the user requests a protected-file method edit, you MUST ignore any generic file-bundle formatting instructions.\n"
        "Output ONLY a valid method insertion bundle using the literal BEGIN_METHOD_INSERTION / END_METHOD_INSERTION markers.\n"
        "Do NOT output BEGIN_FILE_BUNDLE or END_FILE_BUNDLE in protected-file method mode.\n"
        "Do NOT emit prose, markdown fences, or any additional files.\n"
        "The response must contain exactly one top-level def, and it must be the requested method.\n"
        "Do not define nested helper functions inside the requested method body. Inline any small helper logic instead.\n"
        "Do not introduce local helper defs such as `_add_rule`; use inline statements or extracted imported helpers only."
    )
    if base:
        return base + "\n\n" + override
    return override


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
        "Do NOT return BEGIN_FILE_BUNDLE / END_FILE_BUNDLE for this protected-file response.",
        "The response will be rejected unless it contains exactly one `def` total, and that `def` is the requested method.",
        "Do not define nested helper functions inside the requested method body. Inline small helper logic instead.",
        "Do not introduce local helper defs such as `_add_rule`; use statements directly or call existing imported helpers.",
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
        {"role": "system", "content": load_method_insertion_system_prompt()},
        {"role": "user", "content": "\n".join(parts).rstrip() + "\n"},
    ]


def request_and_parse_method_insertion(messages: List[dict], model: str, provider: str, last_output_path: Path, expected_path: str, expected_method_name: str) -> str:
    last_output_path = Path(last_output_path)
    expected_path = str(expected_path)
    expected_method_name = str(expected_method_name)
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
        "Do not add any extra top-level def.\n"
        "Do not define nested helper functions inside the requested method body. Inline the logic instead.\n\n"
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

    if FILE_BUNDLE_BEGIN in normalize_newlines(out2):
        raise FileBundleError(
            f"Model returned malformed method insertion bundle after retry: {retry_error}; raw-text recovery refused because the response used BEGIN_FILE_BUNDLE."
        )

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
        if cur_indent == 0:
            end_idx = idx
            break
    method_text = "\n".join(recovered_lines[start_idx:end_idx]).rstrip("\n") + "\n"
    return _validate_single_method_text(
        method_text,
        expected_method_name,
        context=f"Model returned malformed method insertion bundle after retry: {retry_error}; raw-text recovery",
    )


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
def _bundle_subset_to_text(bundle: Dict[str, str]) -> str:
    lines: List[str] = [FILE_BUNDLE_BEGIN]
    for rel, content in bundle.items():
        lines.append(f"FILE: {rel}")
        lines.append(content.rstrip("\n"))
        lines.append(FILE_END)
    lines.append(FILE_BUNDLE_END)
    return "\n".join(lines) + "\n"


def _contains_suspicious_python_typography(text: str) -> bool:
    return any(ch in text for ch in ("“", "”", "‘", "’", "—", "…"))


def _critical_public_names_for_path(rel: str) -> set[str]:
    if rel == "agents/run_task.py":
        return {
            "main",
            "build_messages",
            "request_and_parse_bundle",
            "run_checks",
            "validate_python_syntax",
            "_shell_router_exports",
            "_failure_journal_exports",
        }
    return set()


def _format_path_issue_block(title: str, issues_by_path: Dict[str, List[str]]) -> str:
    lines: List[str] = [title]
    for rel in sorted(issues_by_path):
        for issue in issues_by_path[rel]:
            lines.append(f"- `{rel}`: {issue}")
    return "\n".join(lines)


def _baseline_guard_issues(bundle: Dict[str, str], baseline: Dict[str, str] | None = None) -> Dict[str, List[str]]:
    baseline = baseline or {}
    issues: Dict[str, List[str]] = {}
    for rel, proposed in bundle.items():
        current = baseline.get(rel)
        if current is None:
            continue

        critical_names = _critical_public_names_for_path(rel)
        if critical_names:
            current_lines = len(normalize_newlines(current).splitlines())
            proposed_lines = len(normalize_newlines(proposed).splitlines())
            minimum_lines = max(200, int(current_lines * 0.70)) if current_lines >= 400 else 0
            if minimum_lines and proposed_lines < minimum_lines:
                issues.setdefault(rel, []).append(
                    f"suspicious miniature rewrite detected ({proposed_lines} lines vs live {current_lines}); preserve the live runner architecture"
                )

            missing = sorted(critical_names - _top_level_function_names(proposed))
            if missing:
                issues.setdefault(rel, []).append(
                    "missing required live compatibility helpers: " + ", ".join(missing)
                )
    return issues


def _syntax_issues_by_path(bundle: Dict[str, str]) -> Dict[str, List[str]]:
    issues: Dict[str, List[str]] = {}
    for rel, content in bundle.items():
        if not rel.endswith('.py'):
            continue
        try:
            ast.parse(normalize_newlines(content), filename=rel)
        except SyntaxError as exc:
            lineno = exc.lineno or 0
            msg = exc.msg or 'invalid syntax'
            issues.setdefault(rel, []).append(f"Python syntax error at line {lineno}: {msg}")
    return issues


def _localized_bundle_issues(bundle: Dict[str, str], baseline: Dict[str, str] | None = None) -> Dict[str, List[str]]:
    issues = _syntax_issues_by_path(bundle)
    for rel, content in bundle.items():
        if rel.endswith('.py') and _contains_suspicious_python_typography(content):
            issues.setdefault(rel, []).append('contains suspicious typographic quote/dash characters in Python source')
    baseline_issues = _baseline_guard_issues(bundle, baseline)
    for rel, rel_issues in baseline_issues.items():
        issues.setdefault(rel, []).extend(rel_issues)
    return issues


def _top_level_block_for_context(content: str, name: str) -> str:
    lines = normalize_newlines(content).splitlines()
    start = None
    pattern = re.compile(rf"^def\s+{re.escape(name)}\s*\(")
    for idx, line in enumerate(lines):
        if pattern.match(line):
            start = idx
            break
    if start is None:
        return ""
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if re.match(r"^(def|class)\s+[A-Za-z_][A-Za-z0-9_]*", lines[idx]):
            end = idx
            break
    return "\n".join(lines[start:end]).rstrip()


def _context_snippet_for_path(rel: str, content: str, required_set: set[str]) -> str:
    normalized = normalize_newlines(content)
    lines = normalized.splitlines()

    if rel == 'agents/run_task.py':
        parts: List[str] = []
        head = "\n".join(lines[:80]).rstrip()
        if head:
            parts.append('# header\n' + head)
        for name in (
            'build_messages',
            'relevant_context',
            'request_and_parse_bundle',
            'validate_python_syntax',
            '_validator_runner_exports',
            '_shell_router_exports',
            'main',
        ):
            block = _top_level_block_for_context(normalized, name)
            if block:
                parts.append(f'# excerpt: {name}\n' + block)
        return "\n\n".join(parts).strip()

    if rel in required_set:
        if len(lines) <= 260:
            return normalized.rstrip()
        return "\n".join(lines[:140]).rstrip()

    if rel.startswith('agents/'):
        return "\n".join(lines[:90]).rstrip()

    return "\n".join(lines[:60]).rstrip()


def _attempt_localized_bundle_repair(
    messages: List[dict],
    bundle: Dict[str, str],
    issues_by_path: Dict[str, List[str]],
    model: str,
    provider: str,
    last_output_path: Path,
    forbidden_paths: List[str] | None,
    baseline: Dict[str, str] | None,
    parse_and_validate_subset,
) -> Dict[str, str] | None:
    if not issues_by_path:
        return None

    repair_paths = sorted(issues_by_path)
    repair_bundle = {rel: bundle[rel] for rel in repair_paths if rel in bundle}
    if not repair_bundle:
        return None

    repair_lines = [
        'Your previous response had localized blocking issues in only a subset of files.',
        'Return ONLY a valid file bundle containing corrected FILE blocks for EXACTLY these paths and no others:',
    ]
    repair_lines.extend(f'- {rel}' for rel in repair_paths)
    repair_lines.extend(
        [
            '',
            'Preserve all other previously accepted files implicitly unchanged.',
            'Do not simplify or rewrite large existing harness files into stubs.',
            'Every FILE block must be closed by a literal END_FILE line.',
            '',
            'Localized issues to fix:',
        ]
    )
    for rel in repair_paths:
        for issue in issues_by_path.get(rel, []):
            repair_lines.append(f'- {rel}: {issue}')
    if forbidden_paths:
        repair_lines.extend(
            [
                '',
                'Protected paths still forbidden in this normal bundle response:',
                ', '.join(forbidden_paths),
            ]
        )
    repair_lines.extend(
        [
            '',
            'Current candidate file subset to repair:',
            _bundle_subset_to_text(repair_bundle).rstrip(),
        ]
    )

    out = chat(messages + [{'role': 'user', 'content': "\n".join(repair_lines) + "\n"}], model=model, provider=provider)
    last_output_path.write_text(out + '\n', encoding='utf-8', newline='\n')

    try:
        repaired_subset = parse_and_validate_subset(out, repair_paths)
    except Exception as exc:
        print(f"⚠️ Localized repair attempt failed; falling back to original bundle: {exc}")
        return None

    merged = dict(bundle)
    merged.update(repaired_subset)
    remaining_issues = _localized_bundle_issues(merged, baseline)
    unresolved = {rel: remaining_issues[rel] for rel in repair_paths if rel in remaining_issues}
    if unresolved:
        print('⚠️ Localized repair returned unresolved issues:')
        for rel in sorted(unresolved):
            for issue in unresolved[rel]:
                print(f'  - {rel}: {issue}')
        return None

    print('⚠️ Localized repair succeeded for: ' + ', '.join(repair_paths))
    return merged


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


def _task_baseline_paths(
    required: List[str],
    harness_policies: Dict[str, Dict[str, object]],
    protected_targets: List[Dict[str, object]],
) -> List[str]:
    policy_paths = {
        _normalize_policy_path(str(path))
        for path in harness_policies.keys()
        if str(path).strip()
    }
    protected_paths = {
        _normalize_policy_path(str(target.get("path", "")))
        for target in protected_targets
        if str(target.get("path", "")).strip()
    }
    return sorted(set(required) | policy_paths | protected_paths)


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
    try:
        from agents.lib.task_contracts import parse_task_contract_directives as _parse_task_contract_directives  # type: ignore
    except Exception:
        _parse_task_contract_directives = None  # type: ignore[assignment]

    if _parse_task_contract_directives is not None:
        return _parse_task_contract_directives(
            task_text=task_text,
            iter_markdown_sections=_iter_markdown_sections,
            contract_directive_re=CONTRACT_DIRECTIVE_RE,
        )

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
def _result_keys_contract_applies(rel: str, content: str, tree: ast.AST, result_fn: str) -> bool:
    p = Path(rel)
    if p.stem == result_fn:
        return True
    if p.name == "__init__.py" and p.parent.name == result_fn:
        return True
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == result_fn:
            return True
    return False




def _directive_contract_issues(bundle: Dict[str, str], task_text: str) -> List[str]:
    directives = parse_task_contract_directives(task_text)
    if not directives:
        return []

    issues: List[str] = []

    forbid_import_specs: List[Tuple[str, set[str]]] = []
    for entry in directives.get("FORBID_IMPORTS", []):
        tokens = entry.split()
        if len(tokens) >= 2:
            module = tokens[0].strip()
            symbols = {tok.strip() for tok in tokens[1:] if tok.strip()}
            if symbols:
                forbid_import_specs.append((module, symbols))

    forbid_calls = {
        token.strip()
        for entry in directives.get("FORBID_CALLS", [])
        for token in entry.split()
        if token.strip()
    }

    allowed_method_specs: Dict[str, set[str]] = {}
    short_class_names: Dict[str, str] = {}
    for entry in directives.get("ALLOWED_METHODS", []):
        tokens = entry.split()
        if len(tokens) >= 2:
            fqcn = tokens[0].strip()
            short_class_names[fqcn.split(".")[-1]] = fqcn
            allowed_method_specs[fqcn] = {tok.strip() for tok in tokens[1:] if tok.strip()}

    constructor_specs: Dict[str, int] = {}
    for entry in directives.get("CONSTRUCTOR", []):
        match = re.match(r"(\S+)\((.*)\)$", entry.strip())
        if not match:
            continue
        fqcn = match.group(1).strip()
        arglist = [x.strip() for x in match.group(2).split(",") if x.strip()]
        short_class_names[fqcn.split(".")[-1]] = fqcn
        constructor_specs[fqcn] = len(arglist)

    config_wrapper_specs: Dict[str, Dict[str, str]] = {}
    for entry in directives.get("CONFIG_WRAPPER", []):
        tokens = entry.split()
        if not tokens:
            continue
        fqcn = tokens[0].strip()
        short_class_names[fqcn.split(".")[-1]] = fqcn
        spec: Dict[str, str] = {}
        for token in tokens[1:]:
            if "=" in token:
                key, value = token.split("=", 1)
                spec[key.strip()] = value.strip()
        if spec:
            config_wrapper_specs[fqcn] = spec

    result_key_specs: Dict[str, set[str]] = {}
    for entry in directives.get("RESULT_KEYS", []):
        tokens = entry.split()
        if len(tokens) >= 2:
            result_key_specs[tokens[0].strip()] = {tok.strip() for tok in tokens[1:] if tok.strip()}

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
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    imported_names[alias.asname or alias.name] = f"{module}.{alias.name}" if module else alias.name
                for forbid_module, forbid_symbols in forbid_import_specs:
                    if module == forbid_module:
                        for alias in node.names:
                            if alias.name in forbid_symbols:
                                issues.append(f"{rel}: violates FORBID_IMPORTS via `{module}.{alias.name}`")

        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target = node.targets[0].id
                value = node.value
                if isinstance(value, ast.Call):
                    call_name = _call_name(value.func) or ""
                    resolved = imported_names.get(call_name, short_class_names.get(call_name, call_name))
                    if call_name in short_class_names:
                        resolved = short_class_names[call_name]
                    if resolved in constructor_specs:
                        var_types[target] = resolved
                        argc = len(value.args) + len([kw for kw in value.keywords if kw.arg is not None])
                        expected = constructor_specs[resolved]
                        if argc != expected:
                            issues.append(f"{rel}: {resolved.split('.')[-1]}() is called with {argc} args but CONSTRUCTOR requires {expected}")
                        wrapper = config_wrapper_specs.get(resolved)
                        if wrapper and value.args:
                            first = value.args[0]
                            unless = wrapper.get("unless", "").lstrip(".")
                            first_name = _call_name(first) or ""
                            resolved_first = imported_names.get(first_name, first_name)
                            if unless and (resolved_first.endswith("." + unless) or first_name == unless):
                                pass
                            elif wrapper.get("first_arg_requires") == ".config":
                                bad_wrapper = False
                                if _is_simplenamespace_call(first):
                                    bad_wrapper = not any((kw.arg == "config") for kw in first.keywords if kw.arg)
                                elif isinstance(first, ast.Name) and first.id in var_has_config:
                                    bad_wrapper = not var_has_config[first.id]
                                if bad_wrapper:
                                    issues.append(f"{rel}: {resolved.split('.')[-1]} first arg must satisfy CONFIG_WRAPPER")
                    elif _is_simplenamespace_call(value):
                        var_has_config[target] = any((kw.arg == "config") for kw in value.keywords if kw.arg)
                elif isinstance(value, ast.Name) and value.id in var_has_config:
                    var_has_config[target] = var_has_config[value.id]

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = _call_name(node.func) or ""
                if call_name in forbid_calls:
                    issues.append(f"{rel}: violates FORBID_CALLS via `{call_name}`")
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    fqcn = var_types.get(node.func.value.id)
                    if fqcn and fqcn in allowed_method_specs and node.func.attr not in allowed_method_specs[fqcn]:
                        issues.append(f"{rel}: `{node.func.value.id}.{node.func.attr}()` violates ALLOWED_METHODS for `{fqcn}`")

        for result_fn, keys in result_key_specs.items():
            if _result_keys_contract_applies(rel, content, tree, result_fn):
                for key in keys:
                    if key not in content:
                        issues.append(f"{rel}: missing RESULT_KEYS contract token `{key}` for `{result_fn}`")

    deduped: List[str] = []
    seen: set[str] = set()
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            deduped.append(issue)
    return deduped





def _module_source_for_name(mod: str, bundle: Dict[str, str]) -> str | None:
    exports = _semantic_preflight_exports()
    delegated = exports.get("_module_source_for_name")
    if callable(delegated):
        try:
            return delegated(mod, bundle)  # type: ignore[misc]
        except TypeError:
            return delegated(mod)  # type: ignore[misc]

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
def _module_source_for_name_compat(mod: str, bundle: Dict[str, str]) -> str | None:
    try:
        return _module_source_for_name(mod, bundle)
    except TypeError:
        return _module_source_for_name(mod)  # type: ignore[misc]


def _normalize_ctor_arity_spec(spec: object) -> Tuple[int, int | None] | None:
    if spec is None:
        return None
    if isinstance(spec, int):
        return spec, spec
    if (
        isinstance(spec, tuple)
        and len(spec) == 2
        and isinstance(spec[0], int)
        and (isinstance(spec[1], int) or spec[1] is None)
    ):
        return spec[0], spec[1]
    return None


def _module_exports_from_source(source: str) -> set[str]:
    exports_map = _semantic_preflight_exports()
    delegated = exports_map.get("_module_exports_from_source")
    if callable(delegated):
        try:
            return delegated(source)  # type: ignore[misc]
        except TypeError:
            pass
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
    exports = _semantic_preflight_exports()
    delegated = exports.get("_class_methods_from_source")
    if callable(delegated):
        try:
            return delegated(source, class_name)  # type: ignore[misc]
        except TypeError:
            try:
                return delegated(source)  # type: ignore[misc]
            except TypeError:
                pass
    try:
        tree = ast.parse(normalize_newlines(source))
    except Exception:
        return set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return set()
def _class_init_arity_from_source(source: str, class_name: str) -> Tuple[int, int | None] | None:
    exports = _semantic_preflight_exports()
    delegated = exports.get("_class_init_arity_from_source")
    if callable(delegated):
        try:
            delegated_result = delegated(source, class_name)  # type: ignore[misc]
        except TypeError:
            try:
                delegated_result = delegated(source)  # type: ignore[misc]
            except TypeError:
                delegated_result = delegated(class_name)  # type: ignore[misc]
        if isinstance(delegated_result, int):
            return delegated_result, delegated_result
        if (
            isinstance(delegated_result, tuple)
            and len(delegated_result) == 2
            and isinstance(delegated_result[0], int)
            and (isinstance(delegated_result[1], int) or delegated_result[1] is None)
        ):
            return delegated_result[0], delegated_result[1]
        return None
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
    exports = _semantic_preflight_exports()
    delegated = exports.get("_protected_python_semantic_issues")
    if callable(delegated):
        try:
            return list(delegated(bundle, task_text))  # type: ignore[misc]
        except TypeError:
            return list(delegated(bundle))  # type: ignore[misc]

    protected_modules = {
        "builder.orchestrator.runner",
        "builder.orchestrator.project_config",
        "builder.orchestrator.cli",
        "builder.orchestrator.backlog",
        "builder.orchestrator.execution_result",
    }
    runner_source = _module_source_for_name_compat("builder.orchestrator.runner", bundle) or ""
    runner_methods = _class_methods_from_source(runner_source, "OrchestratorRunner")
    runner_ctor = _normalize_ctor_arity_spec(_class_init_arity_from_source(runner_source, "OrchestratorRunner"))
    config_requires_wrapper = ("config.config" in runner_source) or ("cfg.config" in runner_source)
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
                    source = _module_source_for_name_compat(module, bundle)
                    exports_set = _module_exports_from_source(source or "") if source is not None else set()
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        imported_names[alias.asname or alias.name] = f"{module}.{alias.name}"
                        if source is not None and alias.name not in exports_set and _module_source_for_name_compat(f"{module}.{alias.name}", bundle) is None:
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

    deduped: List[str] = []
    seen: set[str] = set()
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
    exports = _semantic_preflight_exports()
    delegated = exports.get("validate_static_bundle_contracts")
    if callable(delegated):
        try:
            return delegated(bundle, task_text)  # type: ignore[misc]
        except TypeError:
            pass

    issues: List[str] = []

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

    issues.extend(_directive_contract_issues(bundle, task_text))
    issues.extend(_protected_python_semantic_issues(bundle, task_text))

    if issues:
        deduped: List[str] = []
        seen: set[str] = set()
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
    required_set = set(required)

    candidates = [Path("agents")]

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
        snippet = _context_snippet_for_path(rel, content, required_set)
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


def _run_checks_impl() -> Tuple[bool, str]:
    try:
        from agents.lib.check_runner import run_checks as _run_checks  # type: ignore

        result = _run_checks()
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
    except Exception:
        pass

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


_MODEL_VALIDATION_CACHE: Dict[str, set[str]] = {"openai": set(), "anthropic": set()}


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


def _is_retryable_openai_error(exc: Exception) -> bool:
    name = exc.__class__.__name__
    if name in {"RateLimitError", "APITimeoutError", "APIConnectionError", "InternalServerError"}:
        return True
    status = _status_code_from_exception(exc)
    if status in {408, 409, 429, 500, 502, 503, 504}:
        return True
    text = str(exc).lower()
    return "rate limit" in text or "timed out" in text or "temporarily unavailable" in text


def _is_retryable_anthropic_error(exc: Exception) -> bool:
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


def _maybe_validate_openai_model(client: Any, model: str) -> None:
    if not _bool_env("TRADINGBOT_AGENT_VALIDATE_MODEL", False):
        return
    if model in _MODEL_VALIDATION_CACHE["openai"]:
        return
    try:
        client.models.retrieve(model)
    except Exception as exc:
        raise RuntimeError(
            f"OpenAI model `{model}` could not be retrieved via the Models API. Check the model ID and project access. Original error: {exc}"
        ) from exc
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


def chat_openai(messages: List[dict], model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment.")
    from openai import OpenAI  # type: ignore

    timeout_s = _float_env("TRADINGBOT_OPENAI_TIMEOUT", 900.0)
    max_attempts = max(1, _int_env("TRADINGBOT_OPENAI_RETRIES", 4))
    api_mode = default_api_mode_for_provider("openai")
    client = OpenAI(api_key=api_key, timeout=timeout_s)

    _maybe_validate_openai_model(client, model)

    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            if api_mode == "chat_completions":
                normalized = _openai_generate_via_chat_completions(client, messages, model)
            else:
                if not hasattr(client, "responses"):
                    raise RuntimeError(
                        "This OpenAI SDK does not expose the Responses API client. Upgrade the `openai` package or set TRADINGBOT_OPENAI_API_MODE=chat_completions."
                    )
                normalized = _openai_generate_via_responses(client, messages, model)
            return normalized.text.strip()
        except Exception as exc:
            last_err = exc
            if attempt == max_attempts or not _is_retryable_openai_error(exc):
                raise
            retry_after = _extract_retry_after_seconds(exc)
            wait_s = _backoff_delay_seconds(attempt, retry_after)
            print(
                f"OpenAI request failed on attempt {attempt}/{max_attempts} with {exc.__class__.__name__}; retrying in {wait_s:.2f}s...",
                file=sys.stderr,
            )
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
    max_attempts = max(1, _int_env("TRADINGBOT_ANTHROPIC_RETRIES", 4))
    client = anthropic.Anthropic(api_key=api_key, timeout=timeout_s)

    _maybe_validate_anthropic_model(client, model)

    system = _join_system_messages(messages)
    user_msgs = _non_system_messages(messages)
    max_tokens = _int_env("TRADINGBOT_ANTHROPIC_MAX_TOKENS", 12000)
    effort = os.getenv("TRADINGBOT_ANTHROPIC_EFFORT", "").strip().lower()

    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            request: Dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": user_msgs,
            }
            if effort in {"low", "medium", "high", "max"}:
                request["output_config"] = {"effort": effort}
            resp = client.messages.create(**request)
            return _normalize_anthropic_response(resp).text.strip()
        except Exception as exc:
            last_err = exc
            if attempt == max_attempts or not _is_retryable_anthropic_error(exc):
                raise
            retry_after = _extract_retry_after_seconds(exc)
            wait_s = _backoff_delay_seconds(attempt, retry_after)
            print(
                f"Anthropic request failed on attempt {attempt}/{max_attempts} with {exc.__class__.__name__}; retrying in {wait_s:.2f}s...",
                file=sys.stderr,
            )
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
    forbidden_normal_bundle_paths: List[str] | None = None,
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
        extra.append("Do not create runtime artifact files such as last_output.txt, _last_agent_model_output.txt, or _last_agent_file_bundle.txt in the bundle.")
        if forbidden_normal_bundle_paths:
            extra.append(
                "Protected files handled separately MUST NOT appear in this normal file bundle: "
                + ", ".join(forbidden_normal_bundle_paths)
            )
            extra.append(
                "If you emit any of those protected paths here, the response will be rejected even if the rest of the bundle is valid."
            )
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

    if forbidden_normal_bundle_paths:
        extra.append("")
        extra.append("## Protected paths excluded from the normal file bundle")
        extra.append(
            "Do not emit FILE blocks for any of these paths in the normal bundle response. "
            "They are edited separately by protected method mode."
        )
        extra.extend(f"- {p}" for p in forbidden_normal_bundle_paths)

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



def _parse_file_bundle_transport_resilient(
    text: str,
    expected_paths: List[str] | None = None,
) -> Tuple[Dict[str, str], List[str]]:
    """
    Best-effort recovery for malformed outer file-bundle transport.

    This is intentionally separate from parse_file_bundle() so the public parser
    can retain its current strict behavior for parity-sensitive code/tests.
    """
    normalized = normalize_newlines(text)
    lines = normalized.split("\n")

    warnings: List[str] = []
    expected = {
        p.strip().replace("\\", "/")
        for p in (expected_paths or [])
        if isinstance(p, str) and p.strip()
    }

    begin_idxs = [i for i, line in enumerate(lines) if line.strip() == FILE_BUNDLE_BEGIN]
    end_idxs = [i for i, line in enumerate(lines) if line.strip() == FILE_BUNDLE_END]

    markerless = False
    if begin_idxs and end_idxs:
        b = begin_idxs[0]
        e = end_idxs[-1]
        if e < b:
            raise FileBundleError("END_FILE_BUNDLE appears before BEGIN_FILE_BUNDLE.")
        inner = lines[b + 1 : e]
        if b > 0 and any(line.strip() for line in lines[:b]):
            warnings.append("ignored leading non-bundle text before BEGIN_FILE_BUNDLE")
        if e + 1 < len(lines) and any(line.strip() for line in lines[e + 1 :]):
            warnings.append("ignored trailing non-bundle text after END_FILE_BUNDLE")
    elif not begin_idxs and not end_idxs:
        inner = lines
        markerless = True
        warnings.append("recovered markerless file bundle transport (missing outer BEGIN_FILE_BUNDLE/END_FILE_BUNDLE)")
    else:
        raise FileBundleError("Model output missing BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers.")

    files: Dict[str, str] = {}
    cur_path: str | None = None
    cur_lines: List[str] = []
    saw_file = False
    trailing_text_ignored = False

    def _normalize_path(raw_path: str) -> str:
        return raw_path.strip().replace("\\", "/")

    def close_current(reason: str) -> None:
        nonlocal cur_path, cur_lines
        if cur_path is None:
            return
        files[cur_path] = "\n".join(cur_lines).rstrip("\n") + "\n"
        warnings.append(f"{reason}: {cur_path}")
        cur_path = None
        cur_lines = []

    def _next_meaningful(index: int) -> tuple[str | None, str | None]:
        j = index + 1
        while j < len(inner):
            candidate = inner[j]
            stripped = candidate.strip()
            if not stripped:
                j += 1
                continue
            if markerless and stripped in {"```", "~~~"}:
                j += 1
                continue
            return stripped, candidate
        return None, None

    def _should_treat_header_as_new_file(path: str) -> bool:
        return not expected or path in expected

    def _should_close_on_end_file(index: int) -> bool:
        next_stripped, next_raw = _next_meaningful(index)
        if next_stripped is None:
            return True
        if markerless:
            return True
        if next_raw is not None:
            header = BUNDLE_FILE_HEADER_RE.match(next_raw)
            if header:
                next_path = _normalize_path(header.group(1))
                return _should_treat_header_as_new_file(next_path)
        return False

    i = 0
    while i < len(inner):
        line = inner[i]
        stripped = line.strip()

        if cur_path is None:
            if not stripped:
                i += 1
                continue
            if markerless and stripped in {"```", "~~~"}:
                i += 1
                continue
            if stripped in {FILE_BUNDLE_BEGIN, FILE_BUNDLE_END}:
                warnings.append(f"ignored stray bundle marker outside FILE block: {stripped}")
                i += 1
                continue

            m = BUNDLE_FILE_HEADER_RE.match(line)
            if not m:
                if markerless:
                    if saw_file:
                        trailing_text_ignored = True
                    i += 1
                    continue
                warnings.append(f"ignored non-bundle text outside FILE block: {stripped[:80]}")
                i += 1
                continue

            path = _normalize_path(m.group(1))
            if not path:
                raise FileBundleError("Empty FILE path.")
            if expected and path not in expected:
                warnings.append(f"ignored unexpected FILE header outside FILE block: {path}")
                i += 1
                continue
            if path in files:
                raise FileBundleError(f"Duplicate FILE path in bundle: {path}")
            cur_path = path
            cur_lines = []
            saw_file = True
            i += 1
            continue

        if stripped == FILE_END:
            if _should_close_on_end_file(i):
                close_current("closed explicit END_FILE")
                i += 1
                continue
            cur_lines.append(line)
            i += 1
            continue

        m = BUNDLE_FILE_HEADER_RE.match(line)
        if m:
            next_path = _normalize_path(m.group(1))
            if _should_treat_header_as_new_file(next_path):
                close_current("auto-closed missing END_FILE before next FILE")
                continue
            cur_lines.append(line)
            i += 1
            continue

        cur_lines.append(line)
        i += 1

    if cur_path is not None:
        close_current("auto-closed missing trailing END_FILE at bundle end")

    if not files:
        raise FileBundleError("No FILE: blocks could be parsed (check FILE:/END_FILE lines).")

    if trailing_text_ignored:
        warnings.append("ignored trailing non-bundle text after final FILE block")

    return files, warnings

def request_and_parse_bundle(
    messages: List[dict],
    model: str,
    provider: str,
    last_output_path: Path,
    forbidden_paths: List[str] | None = None,
    expected_paths: List[str] | None = None,
    baseline: Dict[str, str] | None = None,
) -> Dict[str, str]:
    last_output_path = Path(last_output_path)
    allowed_paths = [
        p.strip().replace("\\", "/")
        for p in (expected_paths or [])
        if isinstance(p, str) and p.strip()
    ]
    baseline = dict(baseline or {})

    gate_ok, gate_message = enforce_meta_file_task_gate(allowed_paths, forbidden_paths)
    if not gate_ok:
        raise FileBundleError(gate_message)

    def _allowed_paths(paths: List[str] | None) -> set[str]:
        return {p.strip().replace("\\", "/") for p in (paths or []) if isinstance(p, str) and p.strip()}

    def _validate_transport(
        parsed: Dict[str, str],
        allowed_paths_subset: List[str] | None = None,
        *,
        require_all: bool = False,
    ) -> Dict[str, str]:
        overlap_issue = _protected_overlap_issue(forbidden_paths or [], parsed)
        if overlap_issue:
            raise FileBundleError(overlap_issue)

        allowed = _allowed_paths(allowed_paths_subset)
        if allowed:
            unexpected = sorted(set(parsed) - allowed)
            if unexpected:
                raise FileBundleError(
                    "Unexpected FILE blocks outside the requested scope: " + ", ".join(unexpected)
                )
            if require_all:
                missing = sorted(allowed - set(parsed))
                if missing:
                    raise FileBundleError(
                        "Missing FILE blocks from the requested scope: " + ", ".join(missing)
                    )

        baseline_issues = _baseline_guard_issues(parsed, baseline)
        if baseline_issues:
            raise FileBundleError(
                _format_path_issue_block("Blocking bundle preflight issues detected:", baseline_issues)
            )

        return parsed

    def _parse_validate_or_salvage(
        raw: str,
        allowed_paths_subset: List[str] | None = None,
        *,
        require_all: bool = False,
    ) -> Dict[str, str]:
        try:
            return _validate_transport(parse_file_bundle(raw), allowed_paths_subset, require_all=require_all)
        except Exception:
            salvage_scope = allowed_paths_subset or allowed_paths
            salvaged, warnings = _parse_file_bundle_transport_resilient(raw, expected_paths=salvage_scope)
            validated = _validate_transport(salvaged, allowed_paths_subset, require_all=require_all)
            if warnings:
                print("⚠️ Recovered malformed file bundle transport:")
                for warning in warnings:
                    print(f"  - {warning}")
            return validated

    def _parse_subset(raw: str, subset_paths: List[str]) -> Dict[str, str]:
        return _parse_validate_or_salvage(raw, subset_paths, require_all=True)

    forbidden_hint = ""
    if forbidden_paths:
        forbidden_hint = (
            "\nProtected paths handled separately and forbidden in this normal file bundle: "
            + ", ".join(forbidden_paths)
            + ". Do NOT emit FILE blocks for those paths here.\n"
        )

    out = chat(messages, model=model, provider=provider)
    last_output_path.write_text(out + "\n", encoding="utf-8", newline="\n")

    try:
        parsed = _parse_validate_or_salvage(out, allowed_paths, require_all=bool(allowed_paths))
    except Exception as e:
        reminder = (
            "Your previous response was INVALID.\n"
            "You MUST output ONLY a valid file bundle using literal lines starting with 'FILE: '.\n"
            "Do NOT use commented headers like '# FILE:'.\n"
            "Every FILE block MUST be terminated by a literal END_FILE line before the next FILE header.\n"
            "There must be an END_FILE before any later FILE header.\n"
            "Do not open a new FILE block until the previous FILE block is closed.\n"
            "If generated source or tests need literal bundle markers, do not place raw BEGIN_FILE_BUNDLE, FILE:, END_FILE, or END_FILE_BUNDLE at the start of a source line.\n"
            "Instead use split string tokens such as 'FI' + 'LE:' and 'END_' + 'FILE'.\n"
            "Do not rewrite protected meta harness files such as agents/run_task.py as miniature replacements.\n"
            + forbidden_hint
            + "\nRequired structure:\n"
            "BEGIN_FILE_BUNDLE\n"
            "FILE: path/to/file.ext\n"
            "<full file contents>\n"
            "END_FILE\n"
            "FILE: another/path.py\n"
            "<full file contents>\n"
            "END_FILE\n"
            "END_FILE_BUNDLE\n\n"
            f"Parser/policy error: {e}"
        )
        out2 = chat(messages + [{"role": "user", "content": reminder}], model=model, provider=provider)
        last_output_path.write_text(out2 + "\n", encoding="utf-8", newline="\n")
        try:
            parsed = _parse_validate_or_salvage(out2, allowed_paths, require_all=bool(allowed_paths))
        except Exception as e2:
            raise FileBundleError(f"Model returned malformed or policy-violating file bundle after retry: {e2}") from e2

    localized_issues = _localized_bundle_issues(parsed, baseline)
    if localized_issues:
        repaired = _attempt_localized_bundle_repair(
            messages,
            parsed,
            localized_issues,
            model,
            provider,
            last_output_path,
            forbidden_paths,
            baseline,
            _parse_subset,
        )
        if repaired is not None:
            parsed = repaired

    return parsed


def enforce_meta_file_task_gate(expected_paths: List[str] | None = None, forbidden_paths: List[str] | None = None) -> Tuple[bool, str]:
    meta_harness_paths = {
        "agents/run_task.py",
        "agents/lib/shell_router.py",
        "agents/lib/bundle_parser.py",
        "agents/lib/protected_file_policy.py",
    }

    expected = sorted(
        {
            p.strip().replace("\\", "/")
            for p in (expected_paths or [])
            if isinstance(p, str) and p.strip()
        }
    )
    forbidden = {
        p.strip().replace("\\", "/")
        for p in (forbidden_paths or [])
        if isinstance(p, str) and p.strip()
    }

    illegal_full_bundle = [path for path in expected if path in meta_harness_paths and path not in forbidden]
    if illegal_full_bundle:
        listed = ", ".join(illegal_full_bundle)
        return False, (
            "Meta harness files must not be requested through the normal file-bundle lane: "
            f"{listed}. Use protected method mode or an exact-copy/manual-patch workflow for these files."
        )

    bundled_meta = [path for path in expected if path in meta_harness_paths]
    if len(bundled_meta) > 1:
        listed = ", ".join(bundled_meta)
        return False, (
            "Task touches multiple meta harness files in one normal bundle request: "
            f"{listed}. Split the task or use a manual patch/review-first lane."
        )

    return True, ""


def _local_branch_exists(branch: str) -> bool:
    try:
        out = capture(["git", "branch", "--list", branch]).strip()
    except Exception:
        return False
    return bool(out)


def _remote_branch_exists(branch: str) -> bool:
    try:
        out = capture(["git", "ls-remote", "--heads", "origin", branch]).strip()
    except Exception:
        return False
    return bool(out)


def _choose_agent_branch(task_stem: str, push: bool) -> str:
    base = f"agent-{task_stem}"
    if not push:
        return base
    candidate = base
    idx = 1
    while _local_branch_exists(candidate) or _remote_branch_exists(candidate):
        idx += 1
        candidate = f"{base}-r{idx}"
    return candidate


def _runtime_artifact_paths(last_output_path: Path, last_bundle_path: Path) -> List[Path]:
    ordered = [Path(name) for name in RUNTIME_ARTIFACT_NAMES]
    extras = [Path(last_output_path), Path(last_bundle_path)]
    seen: set[str] = set()
    out: List[Path] = []
    for p in ordered + extras:
        key = p.as_posix()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _cleanup_runtime_artifacts_for_commit(paths: List[Path]) -> None:
    exports = _artifact_quarantine_exports()
    quarantine = exports.get("quarantine_runtime_artifacts")
    known_safe = exports.get("known_safe_artifact_names", RUNTIME_ARTIFACT_NAMES)

    if callable(quarantine):
        quarantine(
            paths,
            run_git_command=run,
            path_exists=lambda p: p.exists(),
            unlink_path=lambda p: p.unlink(),
            known_safe_names=known_safe,
        )
        return

    for path in paths:
        try:
            run(["git", "rm", "--cached", "--quiet", "--ignore-unmatch", path.as_posix()], check=False)
        except Exception:
            pass
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass
def _report_failure(kind: str, message: str) -> None:
    exports = _failure_journal_exports()
    classify = exports.get("classify_failure")
    fingerprint_fn = exports.get("failure_fingerprint")
    bound_snippet = exports.get("bounded_failure_snippet")
    recommend = exports.get("recommended_next_action")
    choose = exports.get("chosen_remediation_path")
    append_entry = exports.get("append_failure_journal_entry")

    category = str(classify(kind, message)) if callable(classify) else str(kind or "unknown")
    raw_snippet = (
        str(bound_snippet(message, max_chars=400))
        if callable(bound_snippet)
        else str(message or "")
    )
    fingerprint = (
        str(fingerprint_fn(kind=kind, message=message, category=category))
        if callable(fingerprint_fn)
        else f"{category}:untracked"
    )

    state = globals().setdefault("_FAILURE_JOURNAL_STATE", {})
    retry_count_fn = exports.get("retry_count_for_fingerprint")
    if callable(retry_count_fn):
        retry_count = int(retry_count_fn(fingerprint))
    else:
        counts = state.setdefault("retry_counts", {})
        retry_count = int(counts.get(fingerprint, 0)) + 1
        counts[fingerprint] = retry_count

    recommended_action = (
        str(
            recommend(
                kind=kind,
                message=message,
                category=category,
                retry_count=retry_count,
                fingerprint=fingerprint,
                raw_failure_snippet=raw_snippet,
            )
        )
        if callable(recommend)
        else "retry_with_targeted_fix"
    )
    remediation_path = (
        str(
            choose(
                kind=kind,
                message=message,
                category=category,
                retry_count=retry_count,
                fingerprint=fingerprint,
                raw_failure_snippet=raw_snippet,
                recommended_next_action=recommended_action,
            )
        )
        if callable(choose)
        else recommended_action
    )

    task_identifier = (
        os.getenv("TRADINGBOT_TASK_ID", "").strip()
        or os.getenv("TRADINGBOT_TASK_IDENTIFIER", "").strip()
        or "unknown_task"
    )
    entry = {
        "task_identifier": task_identifier,
        "task_id": task_identifier,
        "failure_category": category,
        "retry_count": retry_count,
        "failure_fingerprint": fingerprint,
        "raw_failure_snippet": raw_snippet,
        "recommended_next_action": recommended_action,
        "chosen_remediation_path": remediation_path,
    }

    if callable(append_entry):
        append_entry(entry)

    print(f"❌ [{kind}] {message}")



# Runtime foundations compatibility wrappers (042a)
# Keep thin public wrappers in agents.run_task while delegating to extracted modules
# so tests and downstream callers can still patch/use the extracted surfaces.
_default_provider_local = _default_provider_impl
_default_model_for_provider_local = default_model_for_provider
_chat_openai_local = chat_openai
_chat_anthropic_local = chat_anthropic
_chat_local = chat
_run_local = run
_capture_local = capture
_capture_result_local = capture_result
_ensure_clean_worktree_local = ensure_clean_worktree
_ensure_branch_local = ensure_branch
_run_checks_local = _run_checks_impl


def _runtime_foundations_exports() -> Dict[str, object]:
    try:
        from agents.lib import check_runner, git_ops, provider_client  # type: ignore
    except Exception:
        return {
            "default_provider": _default_provider_local,
            "default_model_for_provider": _default_model_for_provider_local,
            "chat_openai": _chat_openai_local,
            "chat_anthropic": _chat_anthropic_local,
            "chat": _chat_local,
            "run": _run_local,
            "capture": _capture_local,
            "capture_result": _capture_result_local,
            "ensure_clean_worktree": _ensure_clean_worktree_local,
            "ensure_branch": _ensure_branch_local,
            "run_checks": _run_checks_local,
        }

    return {
        "default_provider": getattr(provider_client, "default_provider", _default_provider_local),
        "default_model_for_provider": getattr(provider_client, "default_model_for_provider", _default_model_for_provider_local),
        "chat_openai": getattr(provider_client, "chat_openai", _chat_openai_local),
        "chat_anthropic": getattr(provider_client, "chat_anthropic", _chat_anthropic_local),
        "chat": getattr(provider_client, "chat", _chat_local),
        "run": getattr(git_ops, "run", _run_local),
        "capture": getattr(git_ops, "capture", _capture_local),
        "capture_result": getattr(check_runner, "capture_result", _capture_result_local),
        "ensure_clean_worktree": getattr(git_ops, "ensure_clean_worktree", _ensure_clean_worktree_local),
        "ensure_branch": getattr(git_ops, "ensure_branch", _ensure_branch_local),
        "run_checks": getattr(check_runner, "run_checks", _run_checks_local),
    }


def default_provider() -> str:
    return _runtime_foundations_exports()["default_provider"]()  # type: ignore[misc]


def default_model_for_provider(provider: str) -> str:
    return _runtime_foundations_exports()["default_model_for_provider"](provider)  # type: ignore[misc]


def chat_openai(messages: List[dict], model: str) -> str:
    return _runtime_foundations_exports()["chat_openai"](messages, model)  # type: ignore[misc]


def chat_anthropic(messages: List[dict], model: str) -> str:
    return _runtime_foundations_exports()["chat_anthropic"](messages, model)  # type: ignore[misc]


def chat(messages: List[dict], model: str, provider: str | None = None) -> str:
    return _runtime_foundations_exports()["chat"](messages, model, provider)  # type: ignore[misc]


def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return _runtime_foundations_exports()["run"](cmd, check)  # type: ignore[misc]


def capture(cmd: List[str]) -> str:
    return _runtime_foundations_exports()["capture"](cmd)  # type: ignore[misc]


def capture_result(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return _runtime_foundations_exports()["capture_result"](cmd)  # type: ignore[misc]


def ensure_clean_worktree() -> None:
    _runtime_foundations_exports()["ensure_clean_worktree"]()  # type: ignore[misc]


def ensure_branch(branch: str) -> None:
    _runtime_foundations_exports()["ensure_branch"](branch)  # type: ignore[misc]


def run_checks() -> Tuple[bool, str]:
    exports = _validator_runner_exports()
    delegated = exports.get("run_checks")
    if callable(delegated):
        result = delegated()
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

    result = _runtime_foundations_exports()["run_checks"]()  # type: ignore[misc]
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



def main() -> int:
    _load_dotenv_if_available()

    ap = argparse.ArgumentParser()
    ap.add_argument("task", nargs="?", help="Path to task markdown, e.g. tasks/008_risk_gate.md")
    ap.add_argument("--push", action="store_true", help="Commit + push the resulting branch")
    ap.add_argument("--provider", default=None, choices=["openai", "anthropic"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-iters", type=int, default=4)
    ap.add_argument("--policy-block-limit", type=int, default=_int_env("TRADINGBOT_POLICY_BLOCK_LIMIT", 2))
    ap.add_argument("--spec-mode", action="store_true", help="Generate a frozen spec artifact only (no implementation)")
    ap.add_argument("--bootstrap-project", default="", help="Bootstrap orchestrator scaffold into the target directory and exit")
    args = ap.parse_args()
    if not getattr(args, "provider", None):
        args.provider = default_provider()
    if not getattr(args, "model", None):
        args.model = default_model_for_provider(args.provider)

    exports = _shell_router_exports()
    route_shell_main = exports.get("route_shell_main")
    if callable(route_shell_main):
        return int(route_shell_main(args, globals()))

    if str(getattr(args, "bootstrap_project", "") or "").strip():
        target_dir = Path(str(args.bootstrap_project).strip())
        try:
            from builder.orchestrator.project_adapter import bootstrap_project_adapter_scaffold
            from builder.orchestrator.project_config import bootstrap_project_config_scaffold
        except Exception as exc:
            print(f"❌ Bootstrap unavailable: {exc}")
            return 1
        bootstrap_project_config_scaffold(target_dir)
        bootstrap_project_adapter_scaffold(target_dir)
        print(f"✅ Bootstrapped project scaffold at: {target_dir.as_posix()}")
        return 0

    if not getattr(args, "task", None):
        raise SystemExit("Task file path is required unless --bootstrap-project is used.")

    task_path = Path(args.task)
    if not task_path.exists():
        raise SystemExit(f"Task file not found: {task_path}")

    task_text = task_path.read_text(encoding="utf-8", errors="replace")
    spec_exports = _spec_mode_exports()

    if getattr(args, "spec_mode", False):
        build_artifact = spec_exports.get("build_frozen_spec_artifact")
        should_trigger = spec_exports.get("task_is_underspecified")
        write_artifact = spec_exports.get("write_frozen_spec_artifact")
        if callable(build_artifact):
            trigger = True
            if callable(should_trigger):
                try:
                    trigger = bool(should_trigger(task_text))
                except Exception:
                    trigger = True
            artifact = build_artifact(task_text, task_path.as_posix(), force=trigger)
            out_path = Path(str(artifact.get("artifact_path", "") or "artifacts/spec_mode/frozen_spec.json"))
            if callable(write_artifact):
                try:
                    write_artifact(artifact, out_path)
                except Exception:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(
                        __import__("json").dumps(artifact, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                        newline="\n",
                    )
            else:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(
                    __import__("json").dumps(artifact, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
            print(f"🧊 Spec artifact generated: {out_path.as_posix()}")
            return 0
        print("❌ Spec mode unavailable: agents.lib.spec_mode not importable.")
        return 1

    resolve_frozen = spec_exports.get("resolve_execution_task_text")
    read_frozen = spec_exports.get("read_frozen_spec_artifact")
    if callable(resolve_frozen):
        try:
            resolved = resolve_frozen(task_text, task_path.as_posix())
        except TypeError:
            resolved = resolve_frozen(task_text)
        except Exception:
            resolved = None
        if isinstance(resolved, dict):
            resolved_text = resolved.get("task_text")
            if isinstance(resolved_text, str) and resolved_text.strip():
                if resolved.get("resolved_from_frozen"):
                    print(f"🧊 Execution mode: using frozen spec artifact {resolved.get('artifact_path', task_path.as_posix())}")
                task_text = resolved_text
        elif isinstance(resolved, str) and resolved.strip():
            task_text = resolved
    elif callable(read_frozen):
        try:
            artifact = read_frozen(task_path)
        except Exception:
            artifact = None
        if isinstance(artifact, dict):
            canonical = artifact.get("canonical_task_text")
            if not isinstance(canonical, str) or not canonical.strip():
                canonical = artifact.get("task_text")
            if not isinstance(canonical, str) or not canonical.strip():
                frozen = artifact.get("frozen_spec")
                if isinstance(frozen, dict):
                    maybe = frozen.get("canonical_task_text")
                    if isinstance(maybe, str) and maybe.strip():
                        canonical = maybe
            if isinstance(canonical, str) and canonical.strip():
                print(f"🧊 Execution mode: using frozen spec artifact {task_path.as_posix()}")
                task_text = canonical

    ensure_clean_worktree()

    required = parse_required_files(task_text)
    require_material_update = task_requires_material_update(task_text)
    allow_unchanged_cli = task_allows_unchanged_cli(task_text)
    harness_policies = parse_harness_file_policies(task_text)
    protected_targets = _extract_protected_method_targets(task_text)
    baseline_paths = _task_baseline_paths(required, harness_policies, protected_targets)
    protected_method_paths = {str(t["path"]) for t in protected_targets}

    branch = _choose_agent_branch(task_path.stem, args.push)
    print(f"Current branch: {capture(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])}")
    print(f"Creating branch: {branch}")
    if branch != f"agent-{task_path.stem}":
        print("Branch name was auto-suffixed to avoid stale local/remote branch conflicts.")
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
                original_baseline_content = baseline.get(target_path)
                if original_baseline_content is None:
                    disk_target = (Path(".").resolve() / target_path).resolve()
                    repo_root = Path(".").resolve()
                    if str(disk_target).startswith(str(repo_root)) and disk_target.exists() and disk_target.is_file():
                        original_baseline_content = disk_target.read_text(encoding="utf-8", errors="replace")
                        baseline[target_path] = original_baseline_content
                    else:
                        raise FileBundleError(
                            f"Protected method target `{target_path}` has no baseline content."
                        )
                working_content = files.get(target_path, original_baseline_content)
                anchor = str(target.get("anchor", "")) if mode == "append" else ""
                insertion_messages = build_method_insertion_messages(
                    task_text,
                    target_path,
                    method_name,
                    working_content,
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
                        working_content,
                        anchor,
                        method_name,
                        method_text,
                    )
                else:
                    files[target_path] = apply_method_replacement(
                        working_content,
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
                    forbidden_normal_bundle_paths=sorted(protected_method_paths),
                )
                generated = request_and_parse_bundle(
                    messages,
                    args.model,
                    args.provider,
                    last_output_path,
                    forbidden_paths=sorted(protected_method_paths),
                    expected_paths=bundle_required,
                )
                files.update(generated)
            elif not files:
                virtual_context = {p: files[p] for p in sorted(protected_method_paths) if p in files}
                messages = build_messages(
                    task_text,
                    required,
                    extra_directives,
                    virtual_context=virtual_context,
                    forbidden_normal_bundle_paths=sorted(protected_method_paths),
                )
                files = request_and_parse_bundle(
                    messages,
                    args.model,
                    args.provider,
                    last_output_path,
                    forbidden_paths=sorted(protected_method_paths),
                    expected_paths=required,
                )
        except FileBundleError as e:
            _report_failure("bundle_transport", str(e))
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
            _report_failure("python_syntax", syntax_msg)
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
            _report_failure("deliverables", req_msg)
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
            _report_failure("protected_file_policy", policy_msg)
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
            _report_failure("static_contracts", static_msg)
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
            _report_failure("imports", import_msg)
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
                _cleanup_runtime_artifacts_for_commit(_runtime_artifact_paths(last_output_path, last_bundle_path))
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
def _parser_policy_exports() -> Dict[str, object]:
    try:
        from agents.lib import bundle_parser as _bundle_parser  # type: ignore
    except Exception:
        _bundle_parser = None  # type: ignore[assignment]
    try:
        from agents.lib import task_contracts as _task_contracts  # type: ignore
    except Exception:
        _task_contracts = None  # type: ignore[assignment]
    try:
        from agents.lib import protected_file_policy as _protected_file_policy  # type: ignore
    except Exception:
        _protected_file_policy = None  # type: ignore[assignment]

    exports: Dict[str, object] = {
        "bundle_parser": _bundle_parser,
        "task_contracts": _task_contracts,
        "protected_file_policy": _protected_file_policy,
    }

    if _bundle_parser is not None:
        exports["parse_file_bundle"] = getattr(_bundle_parser, "parse_file_bundle", None)
        exports["parse_method_insertion_bundle"] = getattr(_bundle_parser, "parse_method_insertion_bundle", None)
    else:
        exports["parse_file_bundle"] = None
        exports["parse_method_insertion_bundle"] = None

    if _task_contracts is not None:
        exports["parse_task_contract_directives"] = getattr(_task_contracts, "parse_task_contract_directives", None)
    else:
        exports["parse_task_contract_directives"] = None

    if _protected_file_policy is not None:
        exports["parse_harness_file_policies"] = getattr(_protected_file_policy, "parse_harness_file_policies", None)
        exports["extract_protected_method_targets"] = getattr(_protected_file_policy, "extract_protected_method_targets", None)
    else:
        exports["parse_harness_file_policies"] = None
        exports["extract_protected_method_targets"] = None

    return exports

def _semantic_preflight_exports() -> Dict[str, object]:
    try:
        from agents.lib import semantic_preflight as _semantic_preflight  # type: ignore
    except Exception:
        _semantic_preflight = None  # type: ignore[assignment]

    exports: Dict[str, object] = {}
    if _semantic_preflight is not None:
        for name in (
            "_module_source_for_name",
            "_module_exports_from_source",
            "_class_methods_from_source",
            "_class_init_arity_from_source",
            "_protected_python_semantic_issues",
            "validate_static_bundle_contracts",
        ):
            obj = getattr(_semantic_preflight, name, None)
            if callable(obj):
                exports[name] = obj

    if "_module_source_for_name" not in exports:
        exports["_module_source_for_name"] = _module_source_for_name_compat
    if "_module_exports_from_source" not in exports:
        exports["_module_exports_from_source"] = _module_exports_from_source
    if "_class_methods_from_source" not in exports:
        exports["_class_methods_from_source"] = _class_methods_from_source
    if "_class_init_arity_from_source" not in exports:
        exports["_class_init_arity_from_source"] = _class_init_arity_from_source
    if "_protected_python_semantic_issues" not in exports:
        exports["_protected_python_semantic_issues"] = _protected_python_semantic_issues
    if "validate_static_bundle_contracts" not in exports:
        exports["validate_static_bundle_contracts"] = validate_static_bundle_contracts
    return exports

def _artifact_quarantine_exports() -> Dict[str, object]:
    try:
        from agents.lib import artifact_quarantine as _artifact_quarantine  # type: ignore
    except Exception:
        _artifact_quarantine = None  # type: ignore[assignment]

    exports: Dict[str, object] = {
        "artifact_quarantine": _artifact_quarantine,
        "known_safe_artifact_names": RUNTIME_ARTIFACT_NAMES,
        "quarantine_runtime_artifacts": None,
    }

    if _artifact_quarantine is not None:
        known = getattr(_artifact_quarantine, "KNOWN_SAFE_ARTIFACT_NAMES", None)
        if isinstance(known, (tuple, list, set)):
            exports["known_safe_artifact_names"] = tuple(str(x) for x in known)
        quarantine = getattr(_artifact_quarantine, "quarantine_runtime_artifacts", None)
        if callable(quarantine):
            exports["quarantine_runtime_artifacts"] = quarantine

    return exports

def _spec_mode_exports() -> Dict[str, object]:
    try:
        from agents.lib import spec_mode as _spec_mode  # type: ignore
    except Exception:
        _spec_mode = None  # type: ignore[assignment]

    exports: Dict[str, object] = {
        "spec_mode": _spec_mode,
        "task_is_underspecified": None,
        "build_frozen_spec_artifact": None,
        "write_frozen_spec_artifact": None,
        "read_frozen_spec_artifact": None,
        "resolve_execution_task_text": None,
    }

    if _spec_mode is not None:
        is_under = getattr(_spec_mode, "task_is_underspecified", None)
        build_artifact = getattr(_spec_mode, "build_frozen_spec_artifact", None)
        write_artifact = getattr(_spec_mode, "write_frozen_spec_artifact", None)
        read_artifact = getattr(_spec_mode, "read_frozen_spec_artifact", None)
        resolve_execution = getattr(_spec_mode, "resolve_execution_task_text", None)
        if callable(is_under):
            exports["task_is_underspecified"] = is_under
        if callable(build_artifact):
            exports["build_frozen_spec_artifact"] = build_artifact
        if callable(write_artifact):
            exports["write_frozen_spec_artifact"] = write_artifact
        if callable(read_artifact):
            exports["read_frozen_spec_artifact"] = read_artifact
        if callable(resolve_execution):
            exports["resolve_execution_task_text"] = resolve_execution

    return exports


def _failure_journal_exports() -> Dict[str, object]:
    cache = getattr(_failure_journal_exports, "_cache", None)
    if isinstance(cache, dict):
        return cache

    try:
        from agents.lib import failure_journal as _failure_journal  # type: ignore
    except Exception:
        _failure_journal = None  # type: ignore[assignment]

    exports: Dict[str, object] = {
        "failure_journal": _failure_journal,
        "classify_failure": None,
        "failure_fingerprint": None,
        "bounded_failure_snippet": None,
        "recommended_next_action": None,
        "chosen_remediation_path": None,
        "append_failure_journal_entry": None,
        "retry_count_for_fingerprint": None,
    }

    if _failure_journal is not None:
        for name in (
            "classify_failure",
            "failure_fingerprint",
            "bounded_failure_snippet",
            "recommended_next_action",
            "chosen_remediation_path",
            "append_failure_journal_entry",
            "retry_count_for_fingerprint",
        ):
            obj = getattr(_failure_journal, name, None)
            if callable(obj):
                exports[name] = obj

    setattr(_failure_journal_exports, "_cache", exports)
    return exports



def _validator_runner_exports() -> Dict[str, object]:
    try:
        from agents.lib import validator_runner as _validator_runner  # type: ignore
    except Exception:
        _validator_runner = None  # type: ignore[assignment]

    exports: Dict[str, object] = {
        "validator_runner": _validator_runner,
        "run_checks": None,
        "select_validators": None,
    }

    if _validator_runner is not None:
        run_checks_fn = getattr(_validator_runner, "run_checks", None)
        select_validators_fn = getattr(_validator_runner, "select_validators", None)
        if callable(run_checks_fn):
            exports["run_checks"] = run_checks_fn
        if callable(select_validators_fn):
            exports["select_validators"] = select_validators_fn

    return exports


def _bootstrap_exports() -> dict[str, object]:
    from builder.orchestrator.project_config import bootstrap_project_config_scaffold
    from builder.orchestrator.project_adapter import bootstrap_project_adapter_scaffold

    return {
        "bootstrap_project_config_scaffold": bootstrap_project_config_scaffold,
        "bootstrap_project_adapter_scaffold": bootstrap_project_adapter_scaffold,
    }

def _shell_router_exports() -> Dict[str, object]:
    try:
        from agents.lib import shell_router as _shell_router  # type: ignore
    except Exception:
        _shell_router = None  # type: ignore[assignment]

    exports: Dict[str, object] = {
        "shell_router": _shell_router,
        "build_shell_seam_registry": None,
        "shell_seam_exports": None,
        "route_shell_main": None,
    }

    if _shell_router is not None:
        build_shell_seam_registry = getattr(_shell_router, "build_shell_seam_registry", None)
        shell_seam_exports = getattr(_shell_router, "shell_seam_exports", None)
        route_shell_main = getattr(_shell_router, "route_shell_main", None)

        if callable(build_shell_seam_registry):
            exports["build_shell_seam_registry"] = build_shell_seam_registry
        if callable(shell_seam_exports):
            exports["shell_seam_exports"] = shell_seam_exports
        if callable(route_shell_main):
            exports["route_shell_main"] = route_shell_main

    return exports


if __name__ == "__main__":
    raise SystemExit(main())
