import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
from openai import OpenAI

# Load .env into THIS process environment (safe: we never read or print values)
load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]

# Hard guardrails: never read these files
DENY_READ_PATTERNS = [
    re.compile(r"(^|/)\.env(\.|$)"),
    re.compile(r"(^|/)\.aws/"),
    re.compile(r"(^|/)id_rsa"),
    re.compile(r"(^|/)\.ssh/"),
    re.compile(r"(^|/)secrets?"),
]

# What we will include as context by default
DEFAULT_CONTEXT_FILES = [
    "SPEC.md",
    "AGENTS.md",
    "pyproject.toml",
    "requirements.txt",
    "config/config.yaml",
    "src/tradingbot/run.py",
    "src/tradingbot/utils/__init__.py",
    ".github/workflows/ci.yml",
    ".github/workflows/ci_required_status.yml",
]


def run(cmd: List[str], cwd: Path = REPO_ROOT, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command (no shell strings)."""
    return subprocess.run(cmd, cwd=str(cwd), check=check, capture_output=True, text=True)


def is_denied(path: str) -> bool:
    p = path.replace("\\", "/")
    return any(r.search(p) for r in DENY_READ_PATTERNS)


def safe_read_text(relpath: str, max_chars: int = 40_000) -> str:
    """Read file content with guardrails."""
    if is_denied(relpath):
        return f"<<DENIED: {relpath}>>"
    fp = (REPO_ROOT / relpath).resolve()
    if not fp.exists() or not fp.is_file():
        return f"<<MISSING: {relpath}>>"
    if REPO_ROOT not in fp.parents and fp != REPO_ROOT:
        return f"<<OUTSIDE_REPO: {relpath}>>"
    txt = fp.read_text(encoding="utf-8", errors="replace")
    if len(txt) > max_chars:
        return txt[:max_chars] + "\n<<TRUNCATED>>\n"
    return txt


def list_tree(subdir: str, max_lines: int = 300) -> str:
    base = (REPO_ROOT / subdir)
    if not base.exists():
        return f"<<MISSING_DIR: {subdir}>>"
    lines = []
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if is_denied(rel) or p.is_dir():
            continue
        lines.append(rel)
        if len(lines) >= max_lines:
            lines.append("<<TRUNCATED_TREE>>")
            break
    return "\n".join(lines)


def extract_commit_message(text: str) -> str:
    m = re.search(r"^COMMIT:\s*(.+)\s*$", text, re.MULTILINE)
    return (m.group(1).strip() if m else "Apply task changes")


def _strip_crlf(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _remove_code_fence_wrappers(raw: str) -> str:
    t = raw.strip()
    if t.startswith("```"):
        first_nl = t.find("\n")
        if first_nl != -1:
            t2 = t[first_nl + 1 :]
            if t2.rstrip().endswith("```"):
                t2 = t2.rstrip()[:-3]
            return t2.strip()
    return t


def normalize_patch(patch_text: str) -> str:
    """Make the patch more `git apply` friendly.

    - Normalize CRLF -> LF
    - Ensure a blank line before each `diff --git` except the first
    - Drop anything after an accidental 'COMMIT:' inside the diff
    - Ensure trailing newline
    """
    s = _strip_crlf(patch_text).strip("\n")

    # Truncate accidental COMMIT: included inside diff body
    commit_idx = s.find("\nCOMMIT:")
    if commit_idx != -1:
        s = s[:commit_idx].rstrip()

    lines = s.split("\n")
    out: List[str] = []
    seen_first = False
    for line in lines:
        if line.startswith("diff --git "):
            if seen_first and (len(out) > 0 and out[-1] != ""):
                out.append("")
            seen_first = True
        out.append(line)

    return "\n".join(out).rstrip() + "\n"


def extract_diff(model_text: str) -> str:
    """Extract a unified diff from model output."""
    raw = _strip_crlf(model_text).strip()

    # Preferred: ```diff ... ```
    m = re.search(r"```diff\s*\n(.*?)\n```", raw, re.DOTALL)
    if m:
        return normalize_patch(m.group(1))

    # If model wrapped whole thing in a fence (not labeled)
    unwrapped = _remove_code_fence_wrappers(raw)
    if unwrapped.startswith("diff --git "):
        return normalize_patch(unwrapped)

    # If model returned pure diff
    if raw.startswith("diff --git "):
        return normalize_patch(raw)

    raise RuntimeError("Model response did not include a diff we could parse.")


def build_prompt(task_file: str, extra_context_files: List[str]) -> Tuple[str, str]:
    sys_prompt = safe_read_text("agents/prompts/system.md", max_chars=50_000)
    task_txt = safe_read_text(task_file, max_chars=50_000)

    ctx_parts: List[str] = []
    ctx_parts.append("## Repo Tree (src/tradingbot)\n" + list_tree("src/tradingbot"))
    ctx_parts.append("## Repo Tree (tests)\n" + list_tree("tests"))
    ctx_parts.append("## Task File\n" + f"FILE: {task_file}\n" + task_txt)

    for f in DEFAULT_CONTEXT_FILES + extra_context_files:
        if (REPO_ROOT / f).exists():
            ctx_parts.append(f"## FILE: {f}\n" + safe_read_text(f))

    context = "\n\n".join(ctx_parts)
    return sys_prompt, f"# Context\n{context}"


def git_current_branch() -> str:
    cp = run(["git", "branch", "--show-current"])
    return cp.stdout.strip()


def git_checkout_new_branch(branch: str) -> None:
    # If branch exists locally, delete it to avoid "already exists" failures.
    exists = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    ).returncode == 0
    if exists:
        run(["git", "branch", "-D", branch], check=False)
    run(["git", "checkout", "-b", branch])


def git_apply_patch(patch_text: str) -> Tuple[bool, str]:
    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "--recount", "--reject", "-"],
        cwd=str(REPO_ROOT),
        input=patch_text,
        text=True,
        capture_output=True,
    )
    ok = proc.returncode == 0
    out = (proc.stdout or "") + (proc.stderr or "")
    return ok, out.strip()


def run_checks() -> Tuple[bool, str]:
    outputs: List[str] = []
    ok = True

    ruff = subprocess.run(["ruff", "check", "."], cwd=str(REPO_ROOT), text=True, capture_output=True)
    outputs.append("## ruff\n" + (ruff.stdout or "") + (ruff.stderr or ""))
    if ruff.returncode != 0:
        ok = False

    env = os.environ.copy()
    # Ensure src/ layout imports work in checks, matching how you run locally.
    env["PYTHONPATH"] = str((REPO_ROOT / "src"))

    pytest = subprocess.run(["pytest", "-q"], cwd=str(REPO_ROOT), text=True, capture_output=True, env=env)
    outputs.append("## pytest\n" + (pytest.stdout or "") + (pytest.stderr or ""))
    if pytest.returncode != 0:
        ok = False

    return ok, "\n".join(outputs).strip()


def cleanup_worktree() -> None:
    # Reset repo to clean state and remove rejects/untracked.
    subprocess.run(["git", "reset", "--hard"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    subprocess.run(["git", "clean", "-fd"], cwd=str(REPO_ROOT), capture_output=True, text=True)


def git_commit_all(message: str) -> None:
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", message])


def git_push(branch: str) -> None:
    run(["git", "push", "-u", "origin", branch])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_file", help="Task markdown file, e.g. tasks/003_market_hours_guard.md")
    ap.add_argument("--branch", default="", help="Branch name. Default: auto from task filename.")
    ap.add_argument("--max-iters", type=int, default=3, help="Max patch iterations.")
    ap.add_argument("--push", action="store_true", help="Push branch to origin when green.")
    ap.add_argument("--extra-context", nargs="*", default=[], help="Extra files to include as context.")
    args = ap.parse_args()

    if not (REPO_ROOT / "agents/prompts/system.md").exists():
        print("Missing agents/prompts/system.md", file=sys.stderr)
        return 2

    if not (REPO_ROOT / args.task_file).exists():
        print(f"Task file not found: {args.task_file}", file=sys.stderr)
        return 2

    if os.getenv("OPENAI_API_KEY", "").strip() == "":
        print("OPENAI_API_KEY is not set in your environment. (Do NOT paste it here.)", file=sys.stderr)
        return 2

    # Require clean working tree
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO_ROOT), text=True, capture_output=True).stdout.strip()
    if dirty:
        print("Working tree is not clean. Commit/stash your changes before running the agent.", file=sys.stderr)
        return 2

    branch = args.branch.strip()
    if not branch:
        base = Path(args.task_file).stem
        branch = f"agent-{base}".replace(" ", "-").lower()

    start_branch = git_current_branch()
    print(f"Current branch: {start_branch}")
    print(f"Creating branch: {branch}")
    git_checkout_new_branch(branch)

    client = OpenAI()

    sys_prompt, user_prompt = build_prompt(args.task_file, args.extra_context)

    last_error = ""
    for i in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {i}/{args.max_iters} ===")

        msg = user_prompt
        if last_error:
            msg += "\n\n# Previous attempt failed\n" + last_error

        resp = client.chat.completions.create(
            model=os.getenv("TRADINGBOT_AGENT_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": msg},
            ],
            temperature=0.2,
        )

        text = resp.choices[0].message.content or ""
        try:
            patch = extract_diff(text)
            commit_msg = extract_commit_message(text)
        except Exception as e:
            last_error = f"Failed to parse model output: {e}\n\nMODEL_OUTPUT:\n{text}"
            cleanup_worktree()
            continue

        ok, apply_out = git_apply_patch(patch)
        if not ok:
            # Save patch to help debugging
            (REPO_ROOT / "_last_agent_patch.diff").write_text(patch, encoding="utf-8")
            last_error = f"git apply failed:\n{apply_out}\n\nPATCH (saved to _last_agent_patch.diff)"
            cleanup_worktree()
            continue

        checks_ok, checks_out = run_checks()
        if not checks_ok:
            last_error = f"Checks failed after applying patch:\n{checks_out}"
            cleanup_worktree()
            continue

        print("\n✅ Checks passed. Committing…")
        git_commit_all(commit_msg)

        if args.push:
            print("🚀 Pushing branch…")
            git_push(branch)
            print(f"Done. Open PR from branch: {branch}")
        else:
            print("Push skipped (use --push to push).")

        return 0

    print("\n❌ Failed to reach green within max iterations.", file=sys.stderr)
    print(last_error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
