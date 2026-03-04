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
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

FILE_BUNDLE_BEGIN = "BEGIN_FILE_BUNDLE"
FILE_BUNDLE_END = "END_FILE_BUNDLE"
FILE_BEGIN_PREFIX = "FILE:"
FILE_END = "END_FILE"


class FileBundleError(ValueError):
    pass


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv()


def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=False)


def capture(cmd: List[str]) -> str:
    cp = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return cp.stdout.strip()


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
    # Strip UTF-8 BOM if present
    return re.sub(r"^\ufeff", "", s)


# Accept either "FILE:" or "# FILE:" as a header line (fallback for model mistakes).
FILE_HEADER_RE = re.compile(r"^\s*(?:#\s*)?FILE:\s*(.+?)\s*$")


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
            buf.append(lines[i])
            i += 1
        if i >= len(lines):
            raise FileBundleError(f"Missing END_FILE for {relpath}.")

        i += 1  # consume END_FILE
        files[relpath] = "\n".join(buf).rstrip("\n") + "\n"

    if not files:
        raise FileBundleError("No FILE: blocks could be parsed (check FILE:/END_FILE lines).")

    return files


def write_files(files: Dict[str, str]) -> None:
    for rel, data in files.items():
        p = Path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data, encoding="utf-8", newline="\n")


DELIVERABLE_PATH_RE = re.compile(r"`([^`]+\.[A-Za-z0-9_]+)`")


def parse_required_files(task_text: str) -> List[str]:
    task_text = normalize_newlines(task_text)
    lower = task_text.lower()

    idx = lower.find("## deliverables")
    if idx == -1:
        idx = lower.find("# deliverables")

    section = task_text if idx == -1 else task_text[idx:]

    req: List[str] = []
    for m in DELIVERABLE_PATH_RE.finditer(section):
        path = m.group(1).strip()
        if path.startswith(("src/", "tests/", "agents/")):
            req.append(path)

    seen = set()
    out: List[str] = []
    for p in req:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


def enforce_required_files(required: List[str], bundle: Dict[str, str]) -> Tuple[bool, str]:
    missing: List[str] = []
    for rf in required:
        # If it's a deliverable, we require it to be in the bundle (so it gets created/updated).
        if rf not in bundle:
            missing.append(rf)

    if not missing:
        return True, ""
    return False, "Missing required deliverables (must be created/updated): " + ", ".join(missing)


def run_checks() -> Tuple[bool, str]:
    details: List[str] = []
    try:
        subprocess.run([sys.executable, "-m", "ruff", "check", "."], check=True, text=True)
    except subprocess.CalledProcessError as e:
        details.append("## ruff\n" + (e.stdout or "") + (e.stderr or ""))
    try:
        subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True, text=True)
    except subprocess.CalledProcessError as e:
        details.append("## pytest\n" + (e.stdout or "") + (e.stderr or ""))
    if details:
        return False, "\n".join(details).strip()
    return True, ""


def load_system_prompt() -> str:
    p = Path("agents/prompts/system.md")
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return "You are an engineering agent. Output ONLY a valid file bundle."


def chat(messages: List[dict], model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment.")
    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(model=model, messages=messages, temperature=0.2)
    return (resp.choices[0].message.content or "").strip()


def build_messages(task_text: str, required: List[str]) -> List[dict]:
    if required:
        req_list = "\n".join(f"- {p}" for p in required)
        task_text = task_text.rstrip() + "\n\n## Required deliverables (must be satisfied)\n" + req_list + "\n"
    return [
        {"role": "system", "content": load_system_prompt().strip()},
        {"role": "user", "content": task_text},
    ]


def main() -> int:
    _load_dotenv_if_available()

    ap = argparse.ArgumentParser()
    ap.add_argument("task", help="Path to task markdown, e.g. tasks/008_risk_gate.md")
    ap.add_argument("--push", action="store_true", help="Commit + push the resulting branch")
    ap.add_argument("--model", default=os.getenv("TRADINGBOT_AGENT_MODEL", "gpt-4o-mini"))
    ap.add_argument("--max-iters", type=int, default=3)
    args = ap.parse_args()

    task_path = Path(args.task)
    if not task_path.exists():
        raise SystemExit(f"Task file not found: {task_path}")

    ensure_clean_worktree()

    task_text = task_path.read_text(encoding="utf-8", errors="replace")
    required = parse_required_files(task_text)

    branch = f"agent-{task_path.stem}"
    print(f"Current branch: {capture(['git','rev-parse','--abbrev-ref','HEAD'])}")
    print(f"Creating branch: {branch}")
    ensure_branch(branch)

    last_output_path = Path("_last_agent_model_output.txt")
    last_bundle_path = Path("_last_agent_file_bundle.txt")

    for it in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {it}/{args.max_iters} ===")
        messages = build_messages(task_text, required)

        out = chat(messages, model=args.model)
        last_output_path.write_text(out + "\n", encoding="utf-8", newline="\n")

        try:
            files = parse_file_bundle(out)
        except Exception:
            reminder = (
                "Your previous response was INVALID. You MUST output ONLY a valid file bundle using literal lines "
                "starting with 'FILE: '. Do NOT use commented headers like '# FILE:'. "
                "Required structure:\n"
                "BEGIN_FILE_BUNDLE\n"
                "FILE: path/to/file.ext\n"
                "<full file contents>\n"
                "END_FILE\n"
                "END_FILE_BUNDLE\n"
                "If there are no changes, output exactly:\nBEGIN_FILE_BUNDLE\nEND_FILE_BUNDLE"
            )
            out2 = chat(messages + [{"role": "user", "content": reminder}], model=args.model)
            last_output_path.write_text(out2 + "\n", encoding="utf-8", newline="\n")
            files = parse_file_bundle(out2)

        # Save parsed bundle for debugging (always as canonical FILE:/END_FILE format)
        pretty: List[str] = [FILE_BUNDLE_BEGIN]
        for p, c in files.items():
            pretty.append(f"FILE: {p}")
            pretty.append(c.rstrip("\n"))
            pretty.append(FILE_END)
        pretty.append(FILE_BUNDLE_END)
        last_bundle_path.write_text("\n".join(pretty) + "\n", encoding="utf-8", newline="\n")

        ok_req, req_msg = enforce_required_files(required, files)
        if not ok_req:
            print(f"❌ {req_msg}")
            # Add a hard requirement reminder into the task for the next iteration
            task_text = task_text.rstrip() + "\n\nIMPORTANT: " + req_msg + "\n"
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
        task_text = task_text.rstrip() + "\n\n# Last run failures\n" + details + "\n"

    print("\n❌ Failed to reach green within max iterations.")
    print("Model output saved to: _last_agent_model_output.txt")
    print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
