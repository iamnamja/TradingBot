import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]

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


def run(cmd: List[str], cwd: Path = REPO_ROOT, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), check=check, capture_output=True, text=True)


def is_denied(path: str) -> bool:
    p = path.replace("\\", "/")
    return any(r.search(p) for r in DENY_READ_PATTERNS)


def safe_read_text(relpath: str, max_chars: int = 50_000) -> str:
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
    base = REPO_ROOT / subdir
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


def _strip_outer_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        nl = t.find("\n")
        if nl != -1:
            body = t[nl + 1 :]
            if body.rstrip().endswith("```"):
                body = body.rstrip()[:-3]
            return body.strip()
    return t


def _strip_commit_lines(diff_text: str) -> str:
    out_lines = []
    for line in diff_text.splitlines():
        if line.startswith("COMMIT:"):
            continue
        out_lines.append(line)
    return "\n".join(out_lines).rstrip() + "\n"


def _ensure_diff_boundaries(diff_text: str) -> str:
    t = diff_text.replace("\r\n", "\n").replace("\r", "\n")
    # Ensure "diff --git" always begins a new line
    t = re.sub(r"(?<!\n)(diff --git )", r"\n\1", t)
    if not t.endswith("\n"):
        t += "\n"
    return t


def _strip_difflib_hint_lines(diff_text: str) -> str:
    lines = diff_text.splitlines()
    out: List[str] = []
    in_hunk = False
    for line in lines:
        if line.startswith("@@"):
            in_hunk = True
            out.append(line)
            continue
        if line.startswith("diff --git "):
            in_hunk = False
            out.append(line)
            continue
        if in_hunk and line.startswith("?"):
            continue
        out.append(line)
    return "\n".join(out).rstrip() + "\n"


def extract_diff(model_text: str) -> str:
    raw = model_text.strip()

    m = re.search(r"```diff\s*\n(.*?)\n```", raw, re.DOTALL)
    if m:
        body = m.group(1)
    else:
        unwrapped = _strip_outer_fence(raw)
        if unwrapped.lstrip().startswith("diff --git "):
            body = unwrapped
        elif raw.startswith("diff --git "):
            body = raw
        else:
            raise RuntimeError("Model response did not include a diff fenced block.")

    body = _ensure_diff_boundaries(body)
    body = _strip_commit_lines(body)
    body = _strip_difflib_hint_lines(body)
    body = _ensure_diff_boundaries(body)
    return body


def extract_commit_message(model_text: str) -> str:
    m = re.search(r"^COMMIT:\s*(.+)\s*$", model_text, re.MULTILINE)
    return (m.group(1).strip() if m else "Apply task changes")


def build_prompt(task_file: str, extra_context_files: List[str]) -> str:
    sys_prompt = safe_read_text("agents/prompts/system.md")
    task_txt = safe_read_text(task_file)

    ctx_parts: List[str] = []
    ctx_parts.append("## Repo Tree (src/tradingbot)\n" + list_tree("src/tradingbot"))
    ctx_parts.append("## Repo Tree (tests)\n" + list_tree("tests"))
    ctx_parts.append(f"## Task File\nFILE: {task_file}\n" + task_txt)

    for f in DEFAULT_CONTEXT_FILES + extra_context_files:
        if (REPO_ROOT / f).exists():
            ctx_parts.append(f"## FILE: {f}\n" + safe_read_text(f))

    context = "\n\n".join(ctx_parts)
    return f"{sys_prompt}\n\n# Context\n{context}"


def git_current_branch() -> str:
    return run(["git", "branch", "--show-current"]).stdout.strip()


def git_checkout_new_branch(branch: str) -> None:
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
    outputs = []
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


def reset_worktree() -> None:
    run(["git", "reset", "--hard", "HEAD"], check=False)
    run(["git", "clean", "-fd"], check=False)


def touched_paths_from_diff(diff_text: str) -> List[str]:
    paths: List[str] = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                b_path = parts[3]
                if b_path.startswith("b/"):
                    paths.append(b_path[2:])
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_file", help="Task markdown file, e.g. tasks/003_market_hours_guard.md")
    ap.add_argument("--branch", default="", help="Branch name. Default: auto from task filename.")
    ap.add_argument("--max-iters", type=int, default=3, help="Max patch iterations.")
    ap.add_argument("--push", action="store_true", help="Push branch to origin when green.")
    ap.add_argument("--extra-context", nargs="*", default=[], help="Extra files to include as context.")
    args = ap.parse_args()

    if os.getenv("OPENAI_API_KEY", "").strip() == "":
        print("OPENAI_API_KEY is not set in your environment. (Do NOT paste it here.)", file=sys.stderr)
        return 2

    if not (REPO_ROOT / args.task_file).exists():
        print(f"Task file not found: {args.task_file}", file=sys.stderr)
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
    prompt = build_prompt(args.task_file, args.extra_context)

    last_error = ""
    for i in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {i}/{args.max_iters} ===")
        reset_worktree()

        user_msg = prompt
        if last_error:
            user_msg += "\n\n# Previous attempt failed\n" + last_error

        resp = client.chat.completions.create(
            model=os.getenv("TRADINGBOT_AGENT_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": "Follow STRICT DIFF MODE exactly. Output only ```diff ... ``` and optional COMMIT line."},
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

        # Task-003 guardrail: keep patch scoped to new module + tests.
        if Path(args.task_file).name == "003_market_hours_guard.md":
            allowed = {
                "src/tradingbot/utils/market_hours.py",
                "tests/test_market_hours_guard.py",
                "tests/conftest.py",
            }
            touched = set(touched_paths_from_diff(patch))
            extra = touched - allowed
            if extra:
                last_error = (
                    "Patch touched disallowed files for Task 003. "
                    f"Touched: {sorted(touched)}. Allowed only: {sorted(allowed)}."
                )
                continue

        ok, apply_out = git_apply_patch(patch)
        if not ok:
            last_error = f"git apply failed:\n{apply_out}\n\nPATCH:\n{patch}"
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
