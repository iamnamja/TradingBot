#!/usr/bin/env python3
"""Generic agent task runner.

Reads a task markdown file, asks an LLM to output a deterministic file bundle,
writes files, runs ruff+pytest, and optionally commits/pushes to an agent branch.
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

FILE_BUNDLE_BEGIN = "BEGIN_FILE_BUNDLE"
FILE_BUNDLE_END = "END_FILE_BUNDLE"
FILE_END = "END_FILE"

DELIVERABLE_PATH_RE = re.compile(r"`([^`]+\.[A-Za-z0-9_]+)`")
FILE_HEADER_RE = re.compile(r"^\s*(?:#\s*)?FILE:\s*(.+?)\s*$")
BULLET_PATH_RE = re.compile(
    r"""^\s*(?:[-*]|\d+[.)])\s+([A-Za-z0-9_./\\-]+\.[A-Za-z0-9_]+)\s*$""",
    re.MULTILINE,
)
INLINE_PATH_RE = re.compile(
    r"""(?<![A-Za-z0-9_./\\-])([A-Za-z0-9_./\\-]+/[A-Za-z0-9_./\\-]+\.[A-Za-z0-9_]+)(?![A-Za-z0-9_./\\-])"""
)

RUFF_UNUSED_IMPORT_RE = re.compile(r"F401 .*? --> ([^\n:]+):(\d+):\d+", re.MULTILINE)
RUFF_BOOL_COMPARE_RE = re.compile(r"E712 .*? --> ([^\n:]+):(\d+):\d+", re.MULTILINE)
RUFF_UNDEFINED_NAME_RE = re.compile(r"F821 Undefined name `([^`]+)`", re.MULTILINE)

PYTEST_TEST_NAME_RE = re.compile(r"_{5,}\s*(.*?)\s*_{5,}")
PYTEST_TEST_FILE_RE = re.compile(r"^(tests/[^\n:]+):(\d+):", re.MULTILINE)
PYTEST_EXACT_MISMATCH_RE = re.compile(r"^E\s+assert\s+(.+?)\s+==\s+(.+)$", re.MULTILINE)

MISSING_ATTR_RE = re.compile(r"AttributeError: '([^']+)' object has no attribute '([^']+)'")
PATH_ERROR_RE = re.compile(r"(?:PermissionError|FileNotFoundError|IsADirectoryError): .*?: '([^']*)'")
MODULE_NOT_FOUND_RE = re.compile(r"ModuleNotFoundError: No module named '([^']+)'")
NAME_ERROR_RE = re.compile(r"NameError: name '([^']+)' is not defined")
KEY_ERROR_RE = re.compile(r"KeyError: '([^']+)'")
CTOR_TYPE_ERROR_RE = re.compile(r"TypeError: ([A-Za-z_][A-Za-z0-9_]*)\.__init__\(\) takes .*", re.MULTILINE)
TAKES_NO_ARGS_RE = re.compile(r"TypeError: ([A-Za-z_][A-Za-z0-9_]*)\(\) takes no arguments")
MISSING_DELIVERABLES_RE = re.compile(r"Missing required deliverables.*?:\s*(.+)")
UNCHANGED_DELIVERABLES_RE = re.compile(r"Required deliverables were included but not materially updated:\s*(.+)")
GENERIC_TASKS_ASSERT_RE = re.compile(r"assert 'tasks/' == 'generic_tasks/'")
DEFAULT_TASK_RUNNER_RE = re.compile(r"default_task_runner")
WIN_ECHO_RE = re.compile(r"FileNotFoundError: \[WinError 2\].*?\n", re.MULTILINE)


class FileBundleError(ValueError):
    pass


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv()


def run(
    cmd: List[str],
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def capture(cmd: List[str]) -> str:
    return run(cmd, check=True, capture_output=True).stdout.strip()


def capture_result(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return run(cmd, check=False, capture_output=True)


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

    if "FILE:" not in body and "# FILE:" not in body:
        raise FileBundleError("No FILE: headers found inside file bundle.")

    files: Dict[str, str] = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        m = FILE_HEADER_RE.match(lines[i])
        if not m:
            i += 1
            continue

        relpath = m.group(1).strip().replace("\\", "/")
        if not relpath:
            raise FileBundleError("Empty FILE: path.")

        i += 1
        buf: List[str] = []
        while i < len(lines) and lines[i].strip("\n") != FILE_END:
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
        rel = rel.replace("\\", "/").lstrip("/")
        p = (repo_root / rel).resolve()
        if not str(p).startswith(str(repo_root)):
            raise ValueError(f"Refusing to write outside repo root: {rel}")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data, encoding="utf-8", newline="\n")


def _deliverables_section(task_text: str) -> str:
    text = normalize_newlines(task_text)
    lines = text.splitlines()

    start_idx = 0
    found = False
    for i, line in enumerate(lines):
        if re.match(r"^\s*#{1,6}\s+deliverables\s*$", line, re.IGNORECASE):
            start_idx = i + 1
            found = True
            break

    if not found:
        return text

    end_idx = len(lines)
    for j in range(start_idx, len(lines)):
        if re.match(r"^\s*#{1,6}\s+\S", lines[j]):
            end_idx = j
            break

    return "\n".join(lines[start_idx:end_idx])


def parse_required_files(task_text: str) -> List[str]:
    section = _deliverables_section(task_text)
    req: List[str] = []

    for m in DELIVERABLE_PATH_RE.finditer(section):
        path = m.group(1).strip().replace("\\", "/")
        if "/" in path and not path.startswith(("http://", "https://")):
            req.append(path)

    for m in BULLET_PATH_RE.finditer(section):
        path = m.group(1).strip().replace("\\", "/")
        if "/" in path and not path.startswith(("http://", "https://")):
            req.append(path)

    for m in INLINE_PATH_RE.finditer(section):
        path = m.group(1).strip().replace("\\", "/")
        if "/" in path and not path.startswith(("http://", "https://")):
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
        "must create or update all",
        "must create or update",
        "must be created/updated",
        "must be updated",
        "must change",
        "must be materially updated",
        "if any one of these three files is not changed, the task is incomplete",
        "if any one of these",
        "materially updated in the same bundle",
    ]
    return any(p in lower for p in phrases)


def existing_file_contents(paths: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for p in paths:
        path = Path(p)
        if path.exists() and path.is_file():
            out[p] = path.read_text(encoding="utf-8", errors="replace")
    return out


def enforce_required_files(
    required: List[str],
    bundle: Dict[str, str],
    baseline: Dict[str, str] | None = None,
    *,
    require_material_update: bool = False,
) -> Tuple[bool, str]:
    missing = [rf for rf in required if rf not in bundle]
    if missing:
        return False, "Missing required deliverables (must be created/updated): " + ", ".join(missing)

    if require_material_update and baseline is not None:
        unchanged: List[str] = []
        for rf in required:
            if rf in baseline and baseline[rf] == bundle[rf]:
                unchanged.append(rf)
        if unchanged:
            return (
                False,
                "Required deliverables were included but not materially updated: " + ", ".join(unchanged),
            )

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

    candidates = [
        Path("tests/conftest.py"),
        Path("agents/prompts/system.md"),
        Path("system.md"),
        Path("agents/run_task.py"),
        Path("run_task.py"),
    ]

    for rf in required:
        p = Path(rf)
        candidates.append(p)
        if p.parent != Path("."):
            for sib in sorted(p.parent.glob("*.py")):
                candidates.append(sib)
            for sib in sorted(p.parent.glob("*.md")):
                candidates.append(sib)

    for impl_root in [Path("src"), Path("tests")]:
        if impl_root.exists():
            for path in sorted(impl_root.rglob("*.py")):
                if len(candidates) > 100:
                    break
                candidates.append(path)

    for p in candidates:
        if not p.exists() or not p.is_file():
            continue
        rel = p.as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        snippet = "\n".join(content.splitlines()[:160])
        lines.append(f"### {rel}\n{snippet}\n")
    return "\n".join(lines).strip()


def module_exists(module_name: str, bundle: Dict[str, str]) -> bool:
    parts = module_name.split(".")
    if len(parts) < 2:
        return True

    file_candidate = Path("src") / Path(*parts).with_suffix(".py")
    pkg_candidate = Path("src") / Path(*parts) / "__init__.py"

    if file_candidate.exists() or pkg_candidate.exists():
        return True

    return file_candidate.as_posix() in bundle or pkg_candidate.as_posix() in bundle


def validate_imports(bundle: Dict[str, str]) -> Tuple[bool, str]:
    bad: List[str] = []
    import_re = import_regex_for_roots()
    for rel, content in bundle.items():
        for mod, _root in import_re.findall(content):
            if not module_exists(mod, bundle):
                bad.append(f"{rel}: imports missing module '{mod}'")
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

    for name in PYTEST_TEST_NAME_RE.findall(details)[:10]:
        lines.append(f"- Pytest failure: `{name}`")

    for path, lineno in sorted(set(PYTEST_TEST_FILE_RE.findall(details))):
        lines.append(
            f"- Modify implementation files to satisfy the failing expectation referenced by `{path}` line {lineno}. "
            "Do not change tests unless the task explicitly requires it."
        )

    for actual, expected in PYTEST_EXACT_MISMATCH_RE.findall(details)[:10]:
        lines.append(
            f"- Exact mismatch: actual `{actual.strip()}` vs expected `{expected.strip()}`. "
            "Change the implementation so the expected value passes exactly."
        )

    for cls, attr in sorted(set(MISSING_ATTR_RE.findall(details))):
        lines.append(
            f"- AttributeError detected: `{cls}` has no `{attr}`. "
            "Do not fabricate optional fields or guessed config members. "
            "Guard the access with `getattr(..., None)` or skip the behavior when the field is not configured."
        )

    for bad_path in sorted(set(PATH_ERROR_RE.findall(details))):
        shown = bad_path if bad_path else "<empty string>"
        lines.append(
            f"- File-path misuse detected: `{shown}` was treated like a writable file. "
            "Do not substitute directory paths or empty strings for optional file paths. "
            "If no valid file path is configured, skip the write or inject an in-memory callback/writer."
        )

    for mod in sorted(set(MODULE_NOT_FOUND_RE.findall(details))):
        lines.append(
            f"- ModuleNotFoundError detected for `{mod}`. Use an existing repo module or create that module/package in the same bundle."
        )

    if GENERIC_TASKS_ASSERT_RE.search(details):
        lines.append(
            "- A test expects `get_generic_project_config()` to return `generic_tasks/`. Preserve that exact compatibility."
        )

    if DEFAULT_TASK_RUNNER_RE.search(details):
        lines.append(
            "- The task requires `task_runner_command` to default to `None`. Do not use `default_task_runner` as a fallback."
        )

    if WIN_ECHO_RE.search(details):
        lines.append(
            "- A Windows subprocess failure suggests the real-execution test is using an unsafe command. "
            "Use a subprocess-safe Python invocation instead of plain `echo`."
        )

    for undefined_name in sorted(set(RUFF_UNDEFINED_NAME_RE.findall(details))):
        lines.append(
            f"- Ruff reports undefined name `{undefined_name}`. Add the missing import or remove the invalid reference."
        )

    for missing_name in sorted(set(NAME_ERROR_RE.findall(details))):
        lines.append(
            f"- Runtime NameError for `{missing_name}`. Fix imports or use safe forward references in type annotations."
        )

    for missing_key in sorted(set(KEY_ERROR_RE.findall(details))):
        lines.append(
            f"- KeyError for `{missing_key}`. Preserve the legacy result contract and include that key when tests expect it."
        )

    for cls in sorted(set(CTOR_TYPE_ERROR_RE.findall(details))):
        lines.append(
            f"- Constructor signature mismatch for `{cls}`. Preserve the existing backward-compatible constructor signature."
        )

    for cls in sorted(set(TAKES_NO_ARGS_RE.findall(details))):
        lines.append(
            f"- `{cls}` must still accept constructor arguments expected by the existing tests."
        )

    if MISSING_DELIVERABLES_RE.search(details):
        lines.append(
            "- Required deliverables are still missing. Materially update every listed deliverable in the same bundle; "
            "do not leave one untouched while only changing another file."
        )

    if UNCHANGED_DELIVERABLES_RE.search(details):
        lines.append(
            "- Required deliverables were included but unchanged. Materially edit every listed deliverable, not just the main implementation file."
        )

    for line in details.splitlines():
        s = line.strip()
        if s.startswith("E       assert ") and " == " in s:
            pretty = s.replace("E       ", "", 1)
            lines.append(
                f"- Pytest reported exact assertion mismatch: `{pretty}`. "
                "Use this exact expected value as the source of truth."
            )

    deduped: List[str] = []
    seen = set()
    for line in lines:
        if line and line not in seen:
            deduped.append(line)
            seen.add(line)
    return "\n".join(deduped)


def bundle_similarity(a: Dict[str, str], b: Dict[str, str]) -> float:
    if not a and not b:
        return 1.0
    keys = sorted(set(a) | set(b))
    a_text = []
    b_text = []
    for k in keys:
        a_text.append(f"FILE:{k}\n{a.get(k, '')}")
        b_text.append(f"FILE:{k}\n{b.get(k, '')}")
    return difflib.SequenceMatcher(None, "\n".join(a_text), "\n".join(b_text)).ratio()


def run_checks() -> Tuple[bool, str]:
    details: List[str] = []

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


def chat(messages: List[dict], model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment.")
    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(model=model, messages=messages, temperature=0.1)
    return (resp.choices[0].message.content or "").strip()


def build_messages(task_text: str, required: List[str]) -> List[dict]:
    extra: List[str] = []

    if required:
        extra.append("## Required deliverables (must be satisfied)")
        extra.extend(f"- {p}" for p in required)
        extra.append("")
        extra.append("## Output requirements")
        extra.append("You MUST emit FILE blocks for every required deliverable path listed above.")
        extra.append("If a deliverable is an existing file, materially update it in the bundle.")
        extra.append("Do not omit test files named in the task.")
        extra.append("")

    extra.append("## Repository map")
    extra.append(repo_map())
    extra.append("")
    extra.append("## Relevant file context")
    extra.append(relevant_context(required) or "(none)")

    user_task = task_text.rstrip() + "\n\n" + "\n".join(extra).rstrip() + "\n"
    return [
        {"role": "system", "content": load_system_prompt().strip()},
        {"role": "user", "content": user_task},
    ]


def main() -> int:
    _load_dotenv_if_available()

    ap = argparse.ArgumentParser()
    ap.add_argument("task", help="Path to task markdown, e.g. tasks/008_risk_gate.md")
    ap.add_argument("--push", action="store_true", help="Commit + push the resulting branch")
    ap.add_argument("--model", default=os.getenv("TRADINGBOT_AGENT_MODEL", "gpt-4o-mini"))
    ap.add_argument("--max-iters", type=int, default=4)
    args = ap.parse_args()

    task_path = Path(args.task)
    if not task_path.exists():
        raise SystemExit(f"Task file not found: {task_path}")

    ensure_clean_worktree()

    task_text = task_path.read_text(encoding="utf-8", errors="replace")
    required = parse_required_files(task_text)
    require_material_update = task_requires_material_update(task_text)

    branch = f"agent-{task_path.stem}"
    print(f"Current branch: {capture(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])}")
    print(f"Creating branch: {branch}")
    ensure_branch(branch)

    last_output_path = Path("_last_agent_model_output.txt")
    last_bundle_path = Path("_last_agent_file_bundle.txt")

    prev_files: Dict[str, str] | None = None
    consecutive_missing_required = 0

    for it in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {it}/{args.max_iters} ===")
        baseline = existing_file_contents(required)
        messages = build_messages(task_text, required)

        out = chat(messages, model=args.model)
        last_output_path.write_text(out + "\n", encoding="utf-8", newline="\n")

        try:
            files = parse_file_bundle(out)
        except Exception as e:
            reminder = (
                "Your previous response was INVALID.\n"
                "You MUST output ONLY a valid file bundle using literal lines starting with 'FILE: '.\n"
                "Do NOT use commented headers like '# FILE:'.\n\n"
                "Required structure:\n"
                "BEGIN_FILE_BUNDLE\n"
                "FILE: path/to/file.ext\n"
                "<full file contents>\n"
                "END_FILE\n"
                "END_FILE_BUNDLE\n\n"
                "If there are no changes, output exactly:\n"
                "BEGIN_FILE_BUNDLE\n"
                "END_FILE_BUNDLE\n\n"
                f"Parser error: {e}"
            )
            out2 = chat(messages + [{"role": "user", "content": reminder}], model=args.model)
            last_output_path.write_text(out2 + "\n", encoding="utf-8", newline="\n")
            files = parse_file_bundle(out2)

        pretty: List[str] = [FILE_BUNDLE_BEGIN]
        for p, c in files.items():
            pretty.append(f"FILE: {p}")
            pretty.append(c.rstrip("\n"))
            pretty.append(FILE_END)
        pretty.append(FILE_BUNDLE_END)
        last_bundle_path.write_text("\n".join(pretty) + "\n", encoding="utf-8", newline="\n")

        ok_req, req_msg = enforce_required_files(
            required,
            files,
            baseline,
            require_material_update=require_material_update,
        )
        if not ok_req:
            print(f"❌ {req_msg}")
            consecutive_missing_required += 1
            task_text = task_text.rstrip() + "\n\nIMPORTANT: " + req_msg + "\n"
            if consecutive_missing_required >= 2 and required:
                task_text += (
                    "\nIMPORTANT: Your next response MUST contain FILE blocks for every one of these exact paths:\n"
                    + "\n".join(f"- {p}" for p in required)
                    + "\nDo not omit any of them.\n"
                )
            prev_files = files
            continue

        consecutive_missing_required = 0

        ok_imports, import_msg = validate_imports(files)
        if not ok_imports:
            print(f"❌ {import_msg}")
            task_text = (
                task_text.rstrip()
                + "\n\nIMPORTANT: "
                + import_msg
                + "\n"
                + missing_module_hints(import_msg)
                + "\n"
            )
            prev_files = files
            continue

        write_files(files)

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
                    "If the failure mentions an optional config field or invalid file path, remove the call or guard it before invoking the helper.\n"
                )

        prev_files = files

    print("\n❌ Failed to reach green within max iterations.")
    print(f"Model output saved to: {last_output_path}")
    print(f"Parsed file bundle saved to: {last_bundle_path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
