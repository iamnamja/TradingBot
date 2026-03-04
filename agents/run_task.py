import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional

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

DEFAULT_CONTEXT_FILES = [
    "SPEC.md",
    "AGENTS.md",
    "pyproject.toml",
    "requirements.txt",
    ".github/workflows/ci.yml",
    ".github/workflows/ci_required_status.yml",
]

LAST_PATCH = "_last_agent_patch.diff"
LAST_PATCH_LF = "_last_agent_patch_lf.diff"
LAST_MODEL_OUTPUT = "_last_agent_model_output.txt"


def run(cmd: List[str], cwd: Path = REPO_ROOT, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command (guardrail: no arbitrary shell strings)."""
    return subprocess.run(cmd, cwd=str(cwd), check=check, capture_output=True, text=True)


def is_denied(path: str) -> bool:
    p = path.replace("\\", "/")
    return any(r.search(p) for r in DENY_READ_PATTERNS)


def safe_read_text(relpath: str, max_chars: int = 30_000) -> str:
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


def list_tree(subdir: str, max_lines: int = 400) -> str:
    base = (REPO_ROOT / subdir)
    if not base.exists():
        return f"<<MISSING_DIR: {subdir}>>"
    lines: List[str] = []
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(REPO_ROOT).as_posix()
        if is_denied(rel) or p.is_dir():
            continue
        lines.append(rel)
        if len(lines) >= max_lines:
            lines.append("<<TRUNCATED_TREE>>")
            break
    return "\n".join(lines)


def _strip_wrapping_fence(text: str) -> str:
    """If the whole response is a single fenced code block, unwrap it."""
    t = text.strip()
    if not t.startswith("```"):
        return t
    first_nl = t.find("\n")
    if first_nl == -1:
        return t
    body = t[first_nl + 1 :]
    # strip trailing fence if present
    if body.rstrip().endswith("```"):
        body = body.rstrip()[:-3]
    return body.strip()


def extract_commit_message(text: str) -> str:
    m = re.search(r"^COMMIT:\s*(.+)\s*$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return "Apply task changes"


def extract_diff(text: str) -> str:
    """
    Extract a unified diff from model output.

    Accept:
    - Properly fenced ```diff ... ```
    - A raw diff starting with 'diff --git'
    - A single wrapped fence (any label) containing a raw diff

    Also strips trailing COMMIT: lines from the diff body.
    """
    raw = text.strip()

    # Save model output for debugging
    (REPO_ROOT / LAST_MODEL_OUTPUT).write_text(raw, encoding="utf-8", errors="replace")

    if raw.startswith("diff --git "):
        diff = raw
    else:
        m = re.search(r"```diff\s*\n(.*?)(?:\n```|$)", raw, re.DOTALL)
        if m:
            diff = m.group(1).strip()
        else:
            unwrapped = _strip_wrapping_fence(raw)
            if unwrapped.startswith("diff --git "):
                diff = unwrapped
            else:
                raise RuntimeError("Model response did not include a diff we could parse.")

    # Strip trailing COMMIT: lines if the model put it inside the diff block.
    diff = re.sub(r"\nCOMMIT:.*\Z", "\n", diff, flags=re.DOTALL).rstrip() + "\n"
    return diff


def _normalize_line_endings(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _recalc_hunk_header(header: str, old_count: int, new_count: int) -> str:
    # header like: @@ -0,0 +1,10 @@ or @@ -12 +12 @@
    m = re.match(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@", header)
    if not m:
        return header
    old_start = int(m.group(1))
    new_start = int(m.group(3))
    return f"@@ -{old_start},{old_count} +{new_start},{new_count} @@"


def _sanitize_hunks(diff_text: str) -> str:
    """
    Fix common LLM diff issues that cause 'corrupt patch':
    - Incorrect hunk line counts in @@ headers.
    - Missing blank line between file sections (ensure a newline before each 'diff --git' after the first).
    """
    lines = diff_text.splitlines()
    out: List[str] = []
    i = 0

    # Ensure each subsequent file diff starts on a new line (git is strict about structure)
    # We'll rebuild and also recalc hunks.
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git "):
            # ensure separator (except first)
            if out and out[-1] != "":
                out.append("")
            out.append(line)
            i += 1
            continue

        if line.startswith("@@ "):
            header = line
            i += 1
            hunk_body: List[str] = []
            while i < len(lines):
                nxt = lines[i]
                if nxt.startswith("diff --git ") or nxt.startswith("@@ "):
                    break
                hunk_body.append(nxt)
                i += 1

            old_cnt = 0
            new_cnt = 0
            for hb in hunk_body:
                if hb.startswith("\\ No newline"):
                    continue
                if hb.startswith(" "):
                    old_cnt += 1
                    new_cnt += 1
                elif hb.startswith("-"):
                    old_cnt += 1
                elif hb.startswith("+"):
                    new_cnt += 1
                else:
                    # Contextless line inside hunk: treat as context
                    old_cnt += 1
                    new_cnt += 1

            out.append(_recalc_hunk_header(header, old_cnt, new_cnt))
            out.extend(hunk_body)
            continue

        out.append(line)
        i += 1

    # Trim leading empty lines
    while out and out[0] == "":
        out.pop(0)

    return "\n".join(out).rstrip() + "\n"


def build_prompt(task_file: str, extra_context_files: List[str]) -> Tuple[str, str]:
    sys_prompt = safe_read_text("agents/prompts/system.md", max_chars=80_000)
    task_txt = safe_read_text(task_file, max_chars=80_000)

    ctx_parts: List[str] = []
    ctx_parts.append("## Repo Tree (src/tradingbot)\n" + list_tree("src/tradingbot"))
    ctx_parts.append("## Repo Tree (tests)\n" + list_tree("tests"))
    ctx_parts.append("## Task File\n" + task_txt)

    for f in DEFAULT_CONTEXT_FILES + extra_context_files:
        if (REPO_ROOT / f).exists():
            ctx_parts.append(f"## FILE: {f}\n" + safe_read_text(f))

    context = "\n\n".join(ctx_parts)
    return sys_prompt, f"# Context\n{context}"


def git_current_branch() -> str:
    return run(["git", "branch", "--show-current"]).stdout.strip()


def git_checkout_new_branch(branch: str) -> None:
    # If already on branch, do nothing
    if git_current_branch() == branch:
        return

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


def git_apply_patch(patch_text: str) -> Tuple[bool, str]:
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


def run_checks() -> Tuple[bool, str]:
    outputs: List[str] = []
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


def hard_clean_worktree() -> None:
    # Reset and clean untracked/reject files between iterations
    subprocess.run(["git", "reset", "--hard"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    subprocess.run(["git", "clean", "-fd"], cwd=str(REPO_ROOT), capture_output=True, text=True)


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
        hard_clean_worktree()

        msg = user_prompt
        if last_error:
            msg += "\n\n# Previous attempt failed\n" + last_error

        resp = client.chat.completions.create(
            model=os.getenv("TRADINGBOT_AGENT_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": msg},
            ],
            temperature=0.1,
        )

        text = resp.choices[0].message.content or ""
        try:
            patch_raw = extract_diff(text)
            commit_msg = extract_commit_message(text)
        except Exception as e:
            last_error = f"Failed to parse model output: {e}\n\nMODEL_OUTPUT:\n{text}"
            continue

        # Normalize and sanitize patch
        patch_lf = _normalize_line_endings(patch_raw)
        patch_sanitized = _sanitize_hunks(patch_lf)

        # Save for debugging
        (REPO_ROOT / LAST_PATCH).write_text(patch_raw, encoding="utf-8", errors="replace")
        (REPO_ROOT / LAST_PATCH_LF).write_text(patch_sanitized, encoding="utf-8", errors="replace")

        ok, apply_out = git_apply_patch(patch_sanitized)
        if not ok:
            last_error = f"git apply failed:\n{apply_out}\n\nPATCH:\n{patch_sanitized}"
            continue

        checks_ok, checks_out = run_checks()
        if not checks_ok:
            last_error = f"Checks failed after applying patch:\n{checks_out}"
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
