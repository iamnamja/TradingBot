#!/usr/bin/env python3
"""
Agent task runner for TradingBot.

Flow (high level):
- Enforce a clean git working tree.
- Create (or recreate) an agent branch for the task.
- Ask the model for a *file bundle* (BEGIN_FILE_BUNDLE/END_FILE_BUNDLE + FILE/END_FILE blocks).
- Write files to the repo.
- Run checks (ruff + pytest).
- If green, optionally commit & push the agent branch.

This runner is intentionally strict about output formatting so we can `git apply`-free
(we write files directly) and avoid cross-platform patch issues (CRLF/LF, diff hint lines, etc.).
"""
from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYSTEM_PROMPT_PATH = REPO_ROOT / "agents" / "prompts" / "system.md"

FILE_BUNDLE_BEGIN = "BEGIN_FILE_BUNDLE"
FILE_BUNDLE_END = "END_FILE_BUNDLE"


# ------------------------- utilities -------------------------

def run(cmd: List[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the CompletedProcess (stdout/stderr captured as text)."""
    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        check=check,
        capture_output=True,
        text=True,
    )


def require_clean_working_tree() -> None:
    res = run(["git", "status", "--porcelain"], check=True)
    if res.stdout.strip():
        raise SystemExit("Working tree is not clean. Commit/stash your changes before running the agent.")


def current_branch() -> str:
    res = run(["git", "branch", "--show-current"], check=True)
    return res.stdout.strip()


def git_reset_to_origin_main() -> None:
    # Assumes origin/main exists. Keeps things deterministic between iterations.
    run(["git", "fetch", "origin"], check=True)
    run(["git", "switch", "main"], check=True)
    run(["git", "reset", "--hard", "origin/main"], check=True)
    run(["git", "clean", "-fd"], check=True)


def git_delete_branch(branch: str) -> None:
    # Works even if branch doesn't exist.
    run(["git", "branch", "-D", branch], check=False)


def git_checkout_new_branch(branch: str) -> None:
    # Create a fresh branch from current HEAD.
    run(["git", "checkout", "-b", branch], check=True)


# ------------------------- OpenAI chat -------------------------

@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str


def openai_chat(cfg: OpenAIConfig, messages: List[Dict[str, str]]) -> str:
    """
    Minimal OpenAI Responses API call via HTTPS without extra deps.
    This keeps the runner self-contained.

    Note: We intentionally don't stream; we want the full text response.
    """
    import json
    import urllib.request

    url = "https://api.openai.com/v1/responses"
    payload = {
        "model": cfg.model,
        "input": messages,
    }
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {cfg.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    j = json.loads(raw)

    # Responses API: best-effort extraction of the "output_text"
    # output_text is present in many SDK examples; fall back to manual extraction.
    if isinstance(j, dict) and "output_text" in j and isinstance(j["output_text"], str):
        return j["output_text"]

    # Fallback: stitch together text parts
    out_parts: List[str] = []
    for item in j.get("output", []):
        for c in item.get("content", []):
            if c.get("type") in ("output_text", "text") and "text" in c:
                out_parts.append(c["text"])
    return "\n".join(out_parts).strip()


# ------------------------- file bundle parsing/writing -------------------------

def parse_file_bundle(text: str) -> Dict[str, str]:
    """
    Expect:

    BEGIN_FILE_BUNDLE
    FILE: path/to/file.py
    <content>
    END_FILE
    FILE: another/path.txt
    <content>
    END_FILE
    END_FILE_BUNDLE
    """
    if FILE_BUNDLE_BEGIN not in text or FILE_BUNDLE_END not in text:
        raise ValueError("Model output missing BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers.")

    start = text.index(FILE_BUNDLE_BEGIN) + len(FILE_BUNDLE_BEGIN)
    end = text.index(FILE_BUNDLE_END)
    body = text[start:end].strip("\n")

    files: Dict[str, List[str]] = {}
    current_path: str | None = None
    current_lines: List[str] = []

    for line in body.splitlines():
        if line.startswith("FILE: "):
            # flush previous
            if current_path is not None:
                files[current_path] = current_lines
            current_path = line[len("FILE: "):].strip()
            current_lines = []
            continue

        if line.strip() == "END_FILE":
            if current_path is None:
                raise ValueError("END_FILE encountered before FILE: header.")
            files[current_path] = current_lines
            current_path = None
            current_lines = []
            continue

        # regular content line
        if current_path is not None:
            current_lines.append(line)

    if current_path is not None:
        raise ValueError(f"Unclosed file block for: {current_path}")

    return {p: "\n".join(lines).rstrip("\n") + "\n" for p, lines in files.items()}


def write_files(files: Dict[str, str]) -> None:
    for rel_path, content in files.items():
        path = (REPO_ROOT / rel_path).resolve()
        if not str(path).startswith(str(REPO_ROOT.resolve())):
            raise ValueError(f"Refusing to write outside repo root: {rel_path}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def save_pretty_bundle(files: Dict[str, str], path: Path) -> None:
    pretty: List[str] = [FILE_BUNDLE_BEGIN]
    for p, c in files.items():
        pretty.append(f"FILE: {p}")
        pretty.append(c.rstrip("\n"))
        pretty.append("END_FILE")
    pretty.append(FILE_BUNDLE_END)
    path.write_text("\n".join(pretty) + "\n", encoding="utf-8", newline="\n")


# ------------------------- checks -------------------------

def run_checks() -> Tuple[bool, str]:
    details: List[str] = []
    ok = True

    ruff = run(["ruff", "check", "."], check=False)
    if ruff.returncode != 0:
        ok = False
        details.append("## ruff\n" + (ruff.stdout + ruff.stderr).strip())

    pytest = run(["pytest", "-q"], check=False)
    if pytest.returncode != 0:
        ok = False
        details.append("## pytest\n" + (pytest.stdout + pytest.stderr).strip())

    return ok, "\n\n".join(details).strip()


# ------------------------- main -------------------------

def build_agent_branch_name(task_path: Path) -> str:
    # tasks/003_market_hours_guard.md -> agent-003_market_hours_guard
    return f"agent-{task_path.stem}"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", help="Path to task markdown file, e.g. tasks/003_market_hours_guard.md")
    parser.add_argument("--push", action="store_true", help="Commit & push agent branch if checks are green")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5-mini"), help="OpenAI model name")
    parser.add_argument("--max-iters", type=int, default=3, help="Max attempts to reach green")
    parser.add_argument("--system", default=str(DEFAULT_SYSTEM_PROMPT_PATH), help="System prompt path")
    parser.add_argument("--extra-context", nargs="*", default=[], help="Extra file paths to append into prompt")
    args = parser.parse_args()

    # Load .env (repo root) to get OPENAI_API_KEY.
    load_dotenv(dotenv_path=REPO_ROOT / ".env", override=False)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY in environment. (Tip: put it in .env and ensure python-dotenv is installed.)")

    cfg = OpenAIConfig(api_key=api_key, model=args.model)

    task_path = (REPO_ROOT / args.task).resolve()
    if not task_path.exists():
        raise SystemExit(f"Task file not found: {task_path}")

    system_path = Path(args.system).resolve()
    if not system_path.exists():
        raise SystemExit(f"System prompt not found: {system_path}")

    require_clean_working_tree()

    print(f"Current branch: {current_branch()}")

    task_text = load_text(task_path)
    system_prompt = load_text(system_path)

    extra = ""
    for p in args.extra_context:
        fp = (REPO_ROOT / p).resolve()
        if fp.exists() and fp.is_file():
            extra += f"\n\n# FILE: {p}\n" + load_text(fp)

    branch = build_agent_branch_name(task_path)
    print(f"Creating branch: {branch}")

    last_output_path = REPO_ROOT / "_last_agent_model_output.txt"
    last_bundle_path = REPO_ROOT / "_last_agent_file_bundle.txt"

    for i in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {i}/{args.max_iters} ===")

        # Reset to origin/main so the agent always starts clean.
        git_reset_to_origin_main()

        # Recreate branch from current HEAD.
        git_delete_branch(branch)
        git_checkout_new_branch(branch)

        user_prompt = task_text
        if extra.strip():
            user_prompt += "\n\n# EXTRA_CONTEXT\n" + extra + "\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        out = openai_chat(cfg, messages)
        last_output_path.write_text(out, encoding="utf-8", newline="\n")

        try:
            files = parse_file_bundle(out)
        except Exception:
            # Retry once with an explicit reminder about markers.
            reminder = (
                "Your previous response was INVALID because it did not include the required "
                "BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers and FILE/END_FILE blocks. "
                "Output ONLY a valid file bundle now. "
                "If there are no changes, output an EMPTY bundle (just BEGIN_FILE_BUNDLE then END_FILE_BUNDLE)."
            )
            out2 = openai_chat(cfg, messages + [{"role": "user", "content": reminder}])
            last_output_path.write_text(out2, encoding="utf-8", newline="\n")
            try:
                files = parse_file_bundle(out2)
            except Exception as e2:
                print(f"Failed to parse/write file bundle: {e2}")
                continue

        save_pretty_bundle(files, last_bundle_path)
        write_files(files)

        ok, details = run_checks()
        if ok:
            print("✅ Green.")
            if args.push:
                run(["git", "add", "-A"], check=True)
                run(["git", "commit", "-m", f"{task_path.stem}: apply agent changes"], check=True)
                run(["git", "push", "-u", "origin", branch], check=True)
                print(f"Pushed branch: {branch}")
                print("Create a PR on GitHub for this branch (repo rules require PR).")
            return 0

        print("❌ Checks failed after applying changes:\n" + details)

    print("\n❌ Failed to reach green within max iterations.")
    print(f"Model output saved to: {last_output_path.name}")
    print(f"Parsed file bundle saved to: {last_bundle_path.name}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
