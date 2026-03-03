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


def _strip_code_fences(text: str) -> str:
    """
    If the whole response is wrapped in a single fenced block, unwrap it.
    Example:
      ```diff
      ...
      ```
    """
    t = text.strip()
    if t.startswith("```"):
        first_nl = t.find("\n")
        if first_nl != -1:
            t2 = t[first_nl + 1 :]
            if t2.rstrip().endswith("```"):
                t2 = t2.rstrip()[: -3]
            return t2.strip()
    return t


def _strip_trailing_commit(text: str) -> str:
    """
    Strip a trailing COMMIT: line from the diff body if a model mistakenly
    included it inside the diff fence.
    """
    # Remove any line that starts with COMMIT: and everything after it
    # (commit should be outside the diff fence)
    m = re.search(r"(?m)^\s*COMMIT:\s*.+\s*$", text)
    if not m:
        return text
    return text[: m.start()].rstrip() + "\n"


def _normalize_hunk_headers(patch: str) -> str:
    """
    Fix common non-git hunk header variants that cause 'corrupt patch':
      @@ -1 +1,2 @@   -> @@ -1,1 +1,2 @@
      @@ -10 +10 @@  -> @@ -10,1 +10,1 @@
      @@ -5,3 +7 @@  -> @@ -5,3 +7,1 @@
    """
    out_lines: list[str] = []
    for line in patch.splitlines():
        # Exact invalid: @@ -A +B,C @@
        m = re.match(r"^(@@)\s+-(\d+)\s+\+(\d+),(\d+)\s+(@@.*)$", line)
        if m:
            out_lines.append(f"{m.group(1)} -{m.group(2)},1 +{m.group(3)},{m.group(4)} {m.group(5)}")
            continue

        # Exact invalid: @@ -A,B +C @@
        m = re.match(r"^(@@)\s+-(\d+),(\d+)\s+\+(\d+)\s+(@@.*)$", line)
        if m:
            out_lines.append(f"{m.group(1)} -{m.group(2)},{m.group(3)} +{m.group(4)},1 {m.group(5)}")
            continue

        # Exact invalid: @@ -A +B @@
        m = re.match(r"^(@@)\s+-(\d+)\s+\+(\d+)\s+(@@.*)$", line)
        if m:
            out_lines.append(f"{m.group(1)} -{m.group(2)},1 +{m.group(3)},1 {m.group(4)}")
            continue

        out_lines.append(line)

    return "\n".join(out_lines) + ("\n" if not patch.endswith("\n") else "")


def sanitize_patch(patch: str) -> str:
    """
    Best-effort patch sanitizer:
    - normalize CRLF
    - strip accidental COMMIT lines from inside diff
    - normalize invalid hunk headers to git-compatible form
    """
    p = patch.replace("\r\n", "\n").replace("\r", "\n")
    p = _strip_trailing_commit(p)
    p = _normalize_hunk_headers(p)
    return p


def extract_diff(text: str) -> str:
    """
    Extract a unified diff from model output.

    Robust behaviors:
    - Accept properly fenced ```diff ... ```
    - If closing fence is missing, treat end-of-message as end-of-diff
    - If response starts with 'diff --git', treat entire response as diff
    """
    raw = text.strip()

    # Case 1: model returned pure diff without fences
    if raw.startswith("diff --git "):
        return sanitize_patch(raw + "\n")

    # Case 2: fenced diff with closing fence
    m = re.search(r"```diff\s*\n(.*?)\n```", raw, re.DOTALL)
    if m:
        return sanitize_patch(m.group(1).strip() + "\n")

    # Case 3: fenced diff but missing closing fence
    start = raw.find("```diff")
    if start != -1:
        nl = raw.find("\n", start)
        if nl == -1:
            raise RuntimeError("Found ```diff but no content after it.")
        body = raw[nl + 1 :].strip()

        end = body.rfind("```")
        if end != -1:
            body = body[:end].strip()

        return sanitize_patch(body + "\n")

    # Case 4: entire message is wrapped in a fence (maybe not labeled diff)
    unwrapped = _strip_code_fences(raw)
    if unwrapped.startswith("diff --git "):
        return sanitize_patch(unwrapped + "\n")

    raise RuntimeError("Model response did not include a diff we could parse.")


def extract_commit_message(text: str) -> str:
    m = re.search(r"^COMMIT:\s*(.+)\s*$", text, re.MULTILINE)
    return (m.group(1).strip() if m else "Apply task changes")


def build_prompt(task_file: str, extra_context_files: list[str]) -> tuple[str, str]:
    sys_prompt = safe_read_text("agents/prompts/system.md", max_chars=50_000)
    task_txt = safe_read_text(task_file, max_chars=50_000)

    ctx_parts: list[str] = []
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
    """
    Create and checkout a new branch.
    If it already exists locally, just checkout.
    """
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
    cp = run(["git", "status", "--porcelain"], check=True)
    if cp.stdout.strip():
        raise RuntimeError("Working tree is not clean. Commit/stash your changes before running the agent.")


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

    try:
        ensure_clean_worktree()
    except Exception as e:
        print(str(e), file=sys.stderr)
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
            # Clean rejects/partial state to keep iterations consistent
            subprocess.run(["git", "reset", "--hard"], cwd=str(REPO_ROOT))
            subprocess.run(["git", "clean", "-fd"], cwd=str(REPO_ROOT))
            continue

        checks_ok, checks_out = run_checks()
        if not checks_ok:
            last_error = f"Checks failed after applying patch:\n{checks_out}"
            # Clean to avoid accumulating broken state across iterations
            subprocess.run(["git", "reset", "--hard"], cwd=str(REPO_ROOT))
            subprocess.run(["git", "clean", "-fd"], cwd=str(REPO_ROOT))
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
