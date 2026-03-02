import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

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
    ".github/workflows/ci.yml",
    ".github/workflows/ci_required_status.yml",
]


def run(cmd: list[str], cwd: Path = REPO_ROOT, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command (guardrail: no arbitrary shell strings)."""
    return subprocess.run(cmd, cwd=str(cwd), check=check, capture_output=True, text=True)


def is_denied(path: str) -> bool:
    p = path.replace("\\", "/")
    return any(r.search(p) for r in DENY_READ_PATTERNS)


def safe_read_text(relpath: str, max_chars: int = 20_000) -> str:
    """Read file content with guardrails."""
    if is_denied(relpath):
        return f"<<DENIED: {relpath}>>"
    fp = (REPO_ROOT / relpath).resolve()
    if not fp.exists() or not fp.is_file():
        return f"<<MISSING: {relpath}>>"
    # Ensure file is inside repo
    if REPO_ROOT not in fp.parents and fp != REPO_ROOT:
        return f"<<OUTSIDE_REPO: {relpath}>>"
    txt = fp.read_text(encoding="utf-8", errors="replace")
    if len(txt) > max_chars:
        return txt[:max_chars] + "\n<<TRUNCATED>>\n"
    return txt


def list_tree(subdir: str, max_lines: int = 300) -> str:
    """List repo tree for context (paths only)."""
    base = (REPO_ROOT / subdir)
    if not base.exists():
        return f"<<MISSING_DIR: {subdir}>>"
    lines: list[str] = []
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if is_denied(rel):
            continue
        if p.is_dir():
            continue
        lines.append(rel)
        if len(lines) >= max_lines:
            lines.append("<<TRUNCATED_TREE>>")
            break
    return "\n".join(lines)


def extract_commit_message(text: str) -> str:
    m = re.search(r"^COMMIT:\s*(.+)\s*$", text, re.MULTILINE)
    return (m.group(1).strip() if m else "Apply task changes")


def _diff_line_ok(line: str) -> bool:
    """Conservatively keep only lines that look like valid git diff output."""
    if line == "":
        return True
    prefixes = (
        "diff --git ",
        "index ",
        "--- ",
        "+++ ",
        "@@ ",
        "new file mode ",
        "deleted file mode ",
        "old mode ",
        "new mode ",
        "similarity index ",
        "rename from ",
        "rename to ",
        "copy from ",
        "copy to ",
        "Binary files ",
        "GIT binary patch",
        "literal ",
        "delta ",
    )
    if line.startswith(prefixes):
        return True
    # hunk content lines begin with space, +, -, or \\
    if line[0] in (" ", "+", "-", "\\"):
        return True
    return False


def _filter_to_diff_only(text: str) -> str:
    """
    Some models append extra commentary after a diff.
    Keep only lines that look like diff output, stopping once we hit non-diff content
    after we have started collecting.
    """
    lines = text.splitlines()
    out: list[str] = []
    started = False
    for ln in lines:
        if ln.startswith("diff --git "):
            started = True
        if not started:
            continue
        if _diff_line_ok(ln):
            out.append(ln)
            continue
        # First non-diff line after starting -> stop (drop any trailing chatter)
        break
    return "\n".join(out).strip() + "\n"


def extract_diff(text: str) -> str:
    """
    Extract a unified diff from model output.

    Accepted forms:
    - Properly fenced ```diff ... ```
    - Raw diff starting with 'diff --git'
    We also sanitize to remove any non-diff trailing chatter.
    """
    raw = (text or "").strip()

    # Preferred: fenced diff
    m = re.search(r"```diff\s*\n(.*?)\n```", raw, re.DOTALL)
    if m:
        return _filter_to_diff_only(m.group(1).strip())

    # Raw diff (unfenced)
    if raw.startswith("diff --git "):
        return _filter_to_diff_only(raw)

    # Sometimes the model wraps the entire response in an unlabeled fence
    if raw.startswith("```"):
        first_nl = raw.find("\n")
        if first_nl != -1:
            body = raw[first_nl + 1 :].rstrip()
            if body.endswith("```"):
                body = body[:-3].rstrip()
            body = body.strip()
            if body.startswith("diff --git "):
                return _filter_to_diff_only(body)

    raise RuntimeError("Model response did not include a diff we could parse.")


def build_prompt(task_file: str, extra_context_files: list[str]) -> tuple[str, str]:
    sys_prompt = safe_read_text("agents/prompts/system.md", max_chars=50_000)
    task_txt = safe_read_text(task_file, max_chars=50_000)

    # Include exact contents of files that models commonly (wrongly) patch, so it cannot assume a stub.
    common_files = [
        "tests/test_smoke.py",
        "src/tradingbot/utils/__init__.py",
    ]

    ctx_parts: list[str] = []
    ctx_parts.append("## Repo Tree (src/tradingbot)\n" + list_tree("src/tradingbot"))
    ctx_parts.append("## Repo Tree (tests)\n" + list_tree("tests"))
    ctx_parts.append("## Task File\n" + f"FILE: {task_file}\n" + task_txt)

    for f in DEFAULT_CONTEXT_FILES + common_files + extra_context_files:
        if (REPO_ROOT / f).exists():
            ctx_parts.append(f"## FILE: {f}\n" + safe_read_text(f))

    context = "\n\n".join(ctx_parts)
    return sys_prompt, f"# Context\n{context}"


def git_current_branch() -> str:
    cp = run(["git", "branch", "--show-current"])
    return cp.stdout.strip()


def git_checkout_new_branch(branch: str) -> None:
    """Create and checkout a new branch. If it exists locally, just checkout it."""
    exists = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    ).returncode == 0

    if exists:
        run(["git", "checkout", branch])
    else:
        run(["git", "checkout", "-b", branch])


def git_apply_patch(patch_text: str) -> tuple[bool, str]:
    """Apply a unified diff patch. Returns (ok, output)."""
    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "--reject", "-"],
        cwd=str(REPO_ROOT),
        input=patch_text,
        text=True,
        capture_output=True,
    )
    ok = proc.returncode == 0
    out = (proc.stdout or "") + (proc.stderr or "")
    return ok, out.strip()


def run_checks() -> tuple[bool, str]:
    """Run ruff and pytest. Returns (ok, combined_output)."""
    outputs: list[str] = []
    ok = True

    ruff = subprocess.run(["ruff", "check", "."], cwd=str(REPO_ROOT), text=True, capture_output=True)
    outputs.append("## ruff\n" + (ruff.stdout or "") + (ruff.stderr or ""))
    if ruff.returncode != 0:
        ok = False

    pytest = subprocess.run(["pytest", "-q"], cwd=str(REPO_ROOT), text=True, capture_output=True)
    outputs.append("## pytest\n" + (pytest.stdout or "") + (pytest.stderr or ""))
    if pytest.returncode != 0:
        ok = False

    return ok, "\n".join(outputs).strip()


def git_commit_all(message: str) -> None:
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", message])


def git_push(branch: str) -> None:
    run(["git", "push", "-u", "origin", branch])


def ensure_clean_worktree() -> None:
    """Fail fast if worktree is dirty (guardrail)."""
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO_ROOT), text=True, capture_output=True)
    if proc.stdout.strip():
        print("Working tree is not clean. Commit/stash your changes before running the agent.", file=sys.stderr)
        raise SystemExit(2)


def clean_worktree_hard() -> None:
    """Hard reset and clean untracked files (used after failed apply)."""
    subprocess.run(["git", "reset", "--hard"], cwd=str(REPO_ROOT), text=True, capture_output=True)
    subprocess.run(["git", "clean", "-fd"], cwd=str(REPO_ROOT), text=True, capture_output=True)


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

    ensure_clean_worktree()

    # Create branch
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

    # Iterative patch loop
    last_error = ""
    for i in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {i}/{args.max_iters} ===")

        user_msg = user_prompt
        if last_error:
            user_msg += "\n\n# Previous attempt failed\n" + last_error

        resp = client.chat.completions.create(
            model=os.getenv("TRADINGBOT_AGENT_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
        )

        text = resp.choices[0].message.content or ""
        try:
            patch = extract_diff(text)
            commit_msg = extract_commit_message(text)
        except Exception as e:
            last_error = f"Failed to parse model output: {e}\n\nMODEL_OUTPUT:\n{text}"
            continue

        ok, apply_out = git_apply_patch(patch)
        if not ok:
            last_error = f"git apply failed:\n{apply_out}\n\nPATCH:\n{patch}"
            clean_worktree_hard()
            continue

        checks_ok, checks_out = run_checks()
        if not checks_ok:
            last_error = f"Checks failed after applying patch:\n{checks_out}"
            clean_worktree_hard()
            continue

        # All good: commit and optionally push
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
