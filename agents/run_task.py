#!/usr/bin/env python3
"""
Agent task runner for TradingBot.

Key change (v15):
- Stop using `git apply` for model output.
- Require the model to output a *file bundle* with full file contents.
  This eliminates "corrupt patch" failures caused by malformed unified diffs.

Usage:
  py agents/run_task.py tasks/003_market_hours_guard.md --push
  py agents/run_task.py tasks/003_market_hours_guard.md --push --extra-context src/tradingbot/run.py tests/test_smoke.py

Environment:
  OPENAI_API_KEY   (required)
  OPENAI_MODEL     (optional, default: gpt-4o-mini)
  OPENAI_BASE_URL  (optional, default: https://api.openai.com/v1)

Notes:
- Creates (or re-creates) a branch: agent-<taskfile_stem>
- Writes files from the model "FILE_BUNDLE" output
- Runs `python -m ruff check .` and `python -m pytest -q`
- If green and --push: commits + pushes branch and prints PR URL hint
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Tuple

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

SYSTEM_PROMPT_PATH = REPO_ROOT / "agents" / "prompts" / "system.md"


def run(cmd: List[str], *, cwd: pathlib.Path = REPO_ROOT, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), check=check, capture_output=True, text=True)


def git_current_branch() -> str:
    return run(["git", "branch", "--show-current"]).stdout.strip()


def git_is_clean() -> bool:
    out = run(["git", "status", "--porcelain"]).stdout.strip()
    return out == ""


def git_checkout_new_branch(branch: str) -> None:
    # If branch already exists locally, delete it to avoid confusing failures.
    existing = run(["git", "branch", "--list", branch]).stdout.strip()
    if existing:
        run(["git", "branch", "-D", branch], check=True)
    run(["git", "checkout", "-b", branch], check=True)


def git_reset_hard_to_origin_main() -> None:
    run(["git", "fetch", "origin"], check=True)
    run(["git", "checkout", "main"], check=True)
    run(["git", "reset", "--hard", "origin/main"], check=True)
    run(["git", "clean", "-fd"], check=True)


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def read_extra_context(paths: List[str]) -> str:
    parts: List[str] = []
    for p in paths:
        rp = (REPO_ROOT / p).resolve()
        if not rp.exists():
            parts.append(f"\n# MISSING FILE: {p}\n")
            continue
        try:
            txt = rp.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            parts.append(f"\n# ERROR READING FILE: {p} :: {e}\n")
            continue
        parts.append(f"\n# FILE: {p}\n{txt}\n")
    return "\n".join(parts).strip()


@dataclass
class OpenAIConfig:
    api_key: str
    base_url: str
    model: str


def load_openai_config() -> OpenAIConfig:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY in environment.")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return OpenAIConfig(api_key=api_key, base_url=base_url, model=model)


def openai_chat(cfg: OpenAIConfig, messages: List[Dict[str, str]]) -> str:
    """
    Minimal Chat Completions client using urllib (no external deps).
    """
    url = f"{cfg.base_url}/chat/completions"
    body = {
        "model": cfg.model,
        "messages": messages,
        "temperature": 0.2,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {cfg.api_key}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    try:
        return payload["choices"][0]["message"]["content"]
    except Exception:
        raise RuntimeError(f"Unexpected OpenAI response: {payload}")


FILE_BUNDLE_BEGIN = "BEGIN_FILE_BUNDLE"
FILE_BUNDLE_END = "END_FILE_BUNDLE"
FILE_HEADER_RE = re.compile(r"^FILE:\s*(.+?)\s*$", re.MULTILINE)


def parse_file_bundle(text: str) -> Dict[str, str]:
    """
    Expected format:

    BEGIN_FILE_BUNDLE
    FILE: path/to/file.py
    <full file content...>
    END_FILE
    FILE: another/file.txt
    <content...>
    END_FILE
    END_FILE_BUNDLE
    """
    if FILE_BUNDLE_BEGIN not in text or FILE_BUNDLE_END not in text:
        raise ValueError("Model output missing BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers.")

    bundle = text.split(FILE_BUNDLE_BEGIN, 1)[1].split(FILE_BUNDLE_END, 1)[0]
    # Normalize newlines (make git + python happy across Windows/macOS)
    bundle = bundle.replace("\r\n", "\n").replace("\r", "\n")

    files: Dict[str, str] = {}
    # Split by FILE: headers
    matches = list(FILE_HEADER_RE.finditer(bundle))
    if not matches:
        raise ValueError("No FILE: headers found inside file bundle.")

    for idx, m in enumerate(matches):
        path = m.group(1).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(bundle)
        content_block = bundle[start:end].strip("\n")
        # Allow optional END_FILE line, strip if present at end
        content_block = re.sub(r"\n?END_FILE\s*$", "", content_block, flags=re.MULTILINE).strip("\n")
        files[path] = content_block + "\n"  # ensure newline at EOF
    return files


def write_files(files: Dict[str, str]) -> None:
    for rel, content in files.items():
        rel = rel.replace("\\", "/").lstrip("/")
        fp = (REPO_ROOT / rel).resolve()
        if not str(fp).startswith(str(REPO_ROOT.resolve())):
            raise ValueError(f"Refusing to write outside repo: {rel}")
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8", newline="\n")


def run_checks(required_files: list[str]) -> Tuple[bool, str]:
    # Ruff
    try:
        ruff = run([sys.executable, "-m", "ruff", "check", "."], check=False)
        if ruff.returncode != 0:
            return False, "## ruff\n" + ruff.stdout + ruff.stderr
    except FileNotFoundError:
        # if ruff isn't installed, treat as failure because CI expects it
        return False, "## ruff\nruff not available in this environment."

    # Pytest
    pytest = run([sys.executable, "-m", "pytest", "-q"], check=False)
    if pytest.returncode != 0:
        return False, "## pytest\n" + pytest.stdout + pytest.stderr

    return True, "All checks passed."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_file", help="Path to task markdown under tasks/")
    ap.add_argument("--push", action="store_true", help="Commit + push branch if checks pass")
    ap.add_argument("--extra-context", nargs="*", default=[], help="Extra repo file paths to include")
    ap.add_argument("--max-iters", type=int, default=3)
    args = ap.parse_args()

    task_path = (REPO_ROOT / args.task_file).resolve()
    if not task_path.exists():
        raise SystemExit(f"Task file not found: {args.task_file}")

    if not git_is_clean():
        raise SystemExit("Working tree is not clean. Commit/stash your changes before running the agent.")

    cfg = load_openai_config()
    system_prompt = read_text(SYSTEM_PROMPT_PATH)
    task_text = read_text(task_path)
    required_files = parse_required_files(task_text)
    extra = read_extra_context(args.extra_context)

    branch = f"agent-{task_path.stem}"
    print(f"Current branch: {git_current_branch()}")
    print(f"Creating branch: {branch}")
    git_checkout_new_branch(branch)

    last_output_path = REPO_ROOT / "_last_agent_model_output.txt"
    last_bundle_path = REPO_ROOT / "_last_agent_file_bundle.txt"

    for i in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {i}/{args.max_iters} ===")
        # Ensure clean workspace each iter
        git_reset_hard_to_origin_main()
        git_checkout_new_branch(branch)

        user_prompt = task_text
        if extra.strip():
            user_prompt += "\n\n# EXTRA_CONTEXT\n" + extra + "\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            out = openai_chat(cfg, messages)
        except Exception as e:
            print(f"OpenAI call failed: {e}")
            continue

        last_output_path.write_text(out, encoding="utf-8", newline="\n")

        try:
            files = parse_file_bundle(out)
            # Keep a copy of the interpreted bundle
            pretty = [FILE_BUNDLE_BEGIN]
            for p, c in files.items():
                pretty.append(f"FILE: {p}")
                pretty.append(c.rstrip("\n"))
                pretty.append("END_FILE")
            pretty.append(FILE_BUNDLE_END)
            last_bundle_path.write_text("\n".join(pretty) + "\n", encoding="utf-8", newline="\n")

            write_files(files)
        except Exception as e:
            msg = str(e)
            # Retry once with an explicit reminder if the model missed the required markers.
            if ("BEGIN_FILE_BUNDLE" in msg) or ("END_FILE_BUNDLE" in msg) or ("markers" in msg):
                reminder = (
                    "Your previous response was INVALID because it did not include the required "
                    "BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers and FILE/END_FILE blocks. "
                    "Output ONLY a valid file bundle now. "
                    "If there are no changes, output an EMPTY bundle (just BEGIN_FILE_BUNDLE then END_FILE_BUNDLE)."
                )
                messages2 = list(messages) + [{"role": "user", "content": reminder}]
                out2 = openai_chat(messages2)
                last_output_path.write_text(out2, encoding="utf-8", newline="\n")
                try:
                    files = parse_file_bundle(out2)
                    pretty = [FILE_BUNDLE_BEGIN]
                    for p, c in files.items():
                        pretty.append(f"FILE: {p}")
                        pretty.append(c.rstrip("\n"))
                        pretty.append("END_FILE")
                    pretty.append(FILE_BUNDLE_END)
                    last_bundle_path.write_text("\n".join(pretty) + "\n", encoding="utf-8", newline="\n")
                    write_files(files)
                except Exception as e2:
                    print(f"Failed to parse/write file bundle (retry): {e2}")
                    continue
            else:
                print(f"Failed to parse/write file bundle: {e}")
                continue

        ok, details = run_checks(required_files)
        if ok:
            print("✅ Green.")
            if args.push:
                run(["git", "add", "-A"], check=True)
                # If the agent produced no changes, 'git commit' exits 1. Treat as success/no-op.
                staged = run(["git", "diff", "--cached", "--quiet"], check=False).returncode
                if staged == 0:
                    print("No changes to commit (agent already green).")
                    return 0
                run(["git", "commit", "-m", f"{task_path.stem}: apply agent changes"], check=True)
                run(["git", "push", "-u", "origin", branch], check=True)
                print(f"Pushed branch: {branch}")
                print("Create a PR on GitHub for this branch (repo rules require PR).")
            return 0
        else:
            print("❌ Checks failed after applying changes:\n" + details)

    print("\n❌ Failed to reach green within max iterations.")
    print(f"Model output saved to: {last_output_path.name}")
    print(f"Parsed file bundle saved to: {last_bundle_path.name}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
def parse_required_files(task_text: str) -> list[str]:
    """
    Extract required deliverable file paths from a task markdown.

    We prefer the ## Deliverables section. If not present, we fall back to any
    backticked paths that start with src/, tests/, agents/, or tasks/.
    """
    # Normalize line endings
    t = task_text.replace("\r\n", "\n").replace("\r", "\n")

    deliverables_block = ""
    m = re.search(r"^##\s+Deliverables\s*$", t, flags=re.M)
    if m:
        # from end of deliverables header to next section header or EOF
        rest = t[m.end():]
        m2 = re.search(r"^##\s+", rest, flags=re.M)
        deliverables_block = rest[: m2.start()] if m2 else rest
    else:
        deliverables_block = t

    # Capture backticked file-ish paths.
    candidates = re.findall(r"`([^`]+)`", deliverables_block)
    required: list[str] = []
    for c in candidates:
        c = c.strip()
        if not c:
            continue
        if c.startswith(("./", ".\\")):
            c = c[2:]
        c = c.replace("\\", "/")
        if not (
            c.startswith("src/")
            or c.startswith("tests/")
            or c.startswith("agents/")
            or c.startswith("tasks/")
        ):
            continue
        # Heuristic: ignore inline code that isn't a file path
        if "/" not in c:
            continue
        # Only accept likely file paths (must contain a dot extension)
        if "." not in pathlib.Path(c).name:
            continue
        required.append(c)

    # De-dupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for r in required:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


