from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_shell_seam_registry() -> dict[str, tuple[str, ...]]:
    return {
        "bootstrap": ("_bootstrap_exports",),
        "spec_mode": (
            "_spec_mode_exports",
            "build_frozen_spec_artifact",
            "task_is_underspecified",
            "write_frozen_spec_artifact",
            "resolve_execution_task_text",
            "read_frozen_spec_artifact",
        ),
        "failure_journal": ("_report_failure",),
        "validator_runner": ("run_checks", "validate_python_syntax", "validate_imports"),
        "artifact_quarantine": (
            "_cleanup_runtime_artifacts_for_commit",
            "_runtime_artifact_paths",
            "restore_file_snapshot",
        ),
        "runtime_foundations": (
            "ensure_clean_worktree",
            "ensure_branch",
            "existing_file_contents",
            "snapshot_file_contents",
            "write_files",
        ),
        "parser_policy": (
            "parse_required_files",
            "task_requires_material_update",
            "task_allows_unchanged_cli",
            "parse_harness_file_policies",
            "enforce_required_files",
            "enforce_harness_file_policies",
            "validate_static_bundle_contracts",
        ),
        "semantic_preflight": ("parse_semantic_failures", "bundle_similarity"),
        "shell_router": (
            "build_messages",
            "build_method_insertion_messages",
            "request_and_parse_bundle",
            "request_and_parse_method_insertion",
            "apply_method_insertion",
            "apply_method_replacement",
            "FILE_BUNDLE_BEGIN",
            "FILE_END",
            "FILE_BUNDLE_END",
        ),
    }

def shell_seam_exports() -> dict[str, tuple[str, ...]]:
    return build_shell_seam_registry()


_PROTECTED_META_HARNESS_PATHS = frozenset({
    "agents/run_task.py",
    "agents/lib/shell_router.py",
    "agents/lib/bundle_parser.py",
    "agents/lib/protected_file_policy.py",
})

PROTECTED_EXECUTION_TARGET_PROFILES = {
    "agents/run_task.py": (
        {"mode": "replace", "method_name": "_partition_required_paths_for_normal_bundle"},
        {"mode": "replace", "method_name": "_emit_failure_artifact_messages"},
    ),
    "agents/lib/shell_router.py": (
        {"mode": "replace", "method_name": "_partition_required_paths_for_normal_bundle"},
        {"mode": "replace", "method_name": "_emit_failure_artifact_messages"},
        {"mode": "replace", "method_name": "route_shell_main"},
    ),
}


def _normalize_paths(paths: list[str] | None = None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in (paths or []):
        if not isinstance(raw, str):
            continue
        path = raw.strip().replace("\\", "/")
        if not path or path in seen:
            continue
        seen.add(path)
        out.append(path)
    return out


def _infer_protected_method_targets_from_required(task_text: str, protected_required: list[str]) -> list[dict[str, object]]:
    del task_text
    inferred: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for path in _normalize_paths(protected_required):
        for spec in PROTECTED_EXECUTION_TARGET_PROFILES.get(path, ()):  # pragma: no branch - tiny deterministic table
            mode = str(spec.get("mode", "")).strip()
            method_name = str(spec.get("method_name", "")).strip()
            if not mode or not method_name:
                continue
            key = (path, mode, method_name)
            if key in seen:
                continue
            seen.add(key)
            inferred.append({"path": path, "mode": mode, "method_name": method_name})
    return inferred


def _partition_required_paths_for_normal_bundle(required: list[str], protected_method_paths: list[str] | set[str] | tuple[str, ...] | None = None) -> tuple[list[str], list[str]]:
    try:
        from agents.lib.task_contracts import partition_required_paths_for_normal_bundle as delegated_partition
    except Exception:
        delegated_partition = None

    normalized_required = _normalize_paths(required)
    normalized_protected_method_paths = _normalize_paths(list(protected_method_paths or []))

    # Partition using a delegated helper if available (preferred), but still run local heuristics.
    normal: list[str] | None = None
    protected: list[str] | None = None
    if callable(delegated_partition):
        try:
            n, p = delegated_partition(
                normalized_required,
                normalized_protected_method_paths,
                protected_meta_harness_paths=_PROTECTED_META_HARNESS_PATHS,
            )
        except TypeError:
            n, p = delegated_partition(normalized_required, normalized_protected_method_paths)
        normal = _normalize_paths(list(n))
        protected = _normalize_paths(list(p))

    # Fallback partition if no delegation or delegation failed to produce values.
    if normal is None or protected is None:
        protected_required = set(normalized_required) & set(_PROTECTED_META_HARNESS_PATHS)
        protected_required.update(p for p in normalized_protected_method_paths if p in _PROTECTED_META_HARNESS_PATHS)
        protected = [p for p in normalized_required if p in protected_required]
        normal = [p for p in normalized_required if p not in protected_required]

    # Lightweight task-scope heuristics: detect broad multi-seam tasks and recommend splitting.
    # Families focus on orchestrator seams and broad shapes only (non-fatal, advisory only).
    families: set[str] = set()
    for p in normalized_required:
        lp = p.lower()
        # Docs and tests
        if lp.endswith(".md") or lp.startswith("docs/") or "/docs/" in lp:
            families.add("docs")
        if lp.startswith("tests/"):
            families.add("tests")
        # Orchestrator CLI and core harness internals
        if p == "agents/run_task.py":
            families.add("orchestrator_cli")
        if lp.startswith("agents/lib/"):
            name = p.split("/")[-1].lower()
            # Coarse-grained seam family hints by filename keywords only.
            if "shell_router" in name:
                families.add("orchestrator_core")
            if "bundle" in name or "protected" in name or "policy" in name or "parser" in name:
                families.add("policy_or_parser")
            if "failure" in name or "journal" in name or "report" in name:
                families.add("failure_journal")
            if "artifact" in name or "quarantine" in name:
                families.add("artifact_quarantine")
            if "runtime" in name or "snapshot" in name or "worktree" in name or "branch" in name:
                families.add("runtime_foundations")
            if "spec" in name:
                families.add("spec_mode")

    if normalized_protected_method_paths:
        families.add("protected_method_mode")

    core_like = {"orchestrator_cli", "orchestrator_core", "policy_or_parser", "failure_journal", "artifact_quarantine", "runtime_foundations", "spec_mode"}
    core_present = families & core_like

    recommend_reasons: list[str] = []
    # Mixing multiple core orchestrator seams tends to be over-broad.
    if len(core_present) >= 2:
        recommend_reasons.append("multiple_orchestrator_seams")
    # Docs plus deep orchestrator internals often warrant separate normalization tasks.
    if "docs" in families and core_present:
        recommend_reasons.append("docs_plus_core")
    # Protected method mode mixed with broad normal file edits can be split for clarity.
    if "protected_method_mode" in families and (core_present or ("docs" in families)) and (bool(normal) and bool(protected)):
        recommend_reasons.append("protected_plus_normal")

    if recommend_reasons:
        # Non-fatal advisory to help users split tasks when appropriate.
        # Keep output concise and deterministic.
        fam_list = ", ".join(sorted(families))
        reason_list = ", ".join(sorted(set(recommend_reasons)))
        print("Recommendation: split this task into focused subtasks.")
        print(f"Detected seam families: {fam_list}")
        print(f"Heuristic triggers: {reason_list}")
        print("Proceeding without enforcing a split.")

    return normal, protected
def _ensure_failure_artifacts(last_output_path: Path, last_bundle_path: Path, *, task_file: str, failure_category: str, protected_files: list[str] | None = None, before_model_output: bool = False, normal_bundle_attempted: bool = False, reason: str = "", protected_execution_attempted: bool = False, mixed_task: bool = False, protected_targets_identified: list[str] | None = None) -> None:
    payload = {
        "task_file": Path(task_file).as_posix(),
        "failure_category": failure_category,
        "protected_files": _normalize_paths(protected_files),
        "before_model_output": bool(before_model_output),
        "normal_bundle_attempted": bool(normal_bundle_attempted),
        "reason": reason,
        "protected_execution_attempted": bool(protected_execution_attempted),
        "mixed_task": bool(mixed_task),
        "protected_targets_identified": _normalize_paths(protected_targets_identified),
    }
    if not last_output_path.exists():
        body = dict(payload)
        body["artifact_kind"] = "model_output_placeholder"
        last_output_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if not last_bundle_path.exists():
        body = dict(payload)
        body["artifact_kind"] = "file_bundle_placeholder"
        last_bundle_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _emit_failure_artifact_messages(shell_globals: dict[str, Any], last_output_path: Path, last_bundle_path: Path, *, task_file: str, failure_category: str, protected_files: list[str] | None = None, before_model_output: bool = False, normal_bundle_attempted: bool = False, reason: str = "", protected_execution_attempted: bool = False, mixed_task: bool = False, protected_targets_identified: list[str] | None = None) -> None:
    try:
        from agents.lib.failure_artifacts import emit_failure_artifact_messages as delegated_emit
    except Exception:
        delegated_emit = None

    if callable(delegated_emit):
        delegated_emit(
            shell_globals=shell_globals,
            last_output_path=last_output_path,
            last_bundle_path=last_bundle_path,
            task_file=task_file,
            failure_category=failure_category,
            protected_files=protected_files,
            before_model_output=before_model_output,
            normal_bundle_attempted=normal_bundle_attempted,
            reason=reason,
            protected_execution_attempted=protected_execution_attempted,
            mixed_task=mixed_task,
            protected_targets_identified=protected_targets_identified,
        )
        return

    delegated = shell_globals.get("_emit_failure_artifact_messages")
    if callable(delegated):
        delegated(
            last_output_path,
            last_bundle_path,
            task_file=task_file,
            failure_category=failure_category,
            protected_files=protected_files,
            before_model_output=before_model_output,
            normal_bundle_attempted=normal_bundle_attempted,
            reason=reason,
            protected_execution_attempted=protected_execution_attempted,
            mixed_task=mixed_task,
            protected_targets_identified=protected_targets_identified,
        )
        return

    _ensure_failure_artifacts(
        last_output_path,
        last_bundle_path,
        task_file=task_file,
        failure_category=failure_category,
        protected_files=protected_files,
        before_model_output=before_model_output,
        normal_bundle_attempted=normal_bundle_attempted,
        reason=reason,
        protected_execution_attempted=protected_execution_attempted,
        mixed_task=mixed_task,
        protected_targets_identified=protected_targets_identified,
    )
    print(f"Model output saved to: {last_output_path}")
    print(f"Parsed file bundle saved to: {last_bundle_path}")

    # Lightweight, advisory-only split heuristic (non-fatal).
    try:
        paths_for_family: list[str] = []
        paths_for_family.extend(_normalize_paths(protected_files))
        paths_for_family.extend(_normalize_paths(protected_targets_identified))

        # Try to glean additional paths from the last parsed bundle artifact if present.
        if last_bundle_path.exists():
            bundle_text = last_bundle_path.read_text(encoding="utf-8", errors="replace")
            if "FILE_BUNDLE_BEGIN" in bundle_text and "FILE_BUNDLE_END" in bundle_text:
                for line in bundle_text.splitlines():
                    if line.startswith("FILE: "):
                        p = line[len("FILE: ") :].strip()
                        if p:
                            paths_for_family.append(p)

        families: set[str] = set()
        for p in _normalize_paths(paths_for_family):
            lp = p.lower()
            if lp.endswith(".md") or lp.startswith("docs/") or "/docs/" in lp:
                families.add("docs")
            if lp.startswith("tests/"):
                families.add("tests")
            if p == "agents/run_task.py":
                families.add("orchestrator_cli")
            if lp.startswith("agents/lib/"):
                name = p.split("/")[-1].lower()
                if "shell_router" in name:
                    families.add("orchestrator_core")
                if "bundle" in name or "protected" in name or "policy" in name or "parser" in name:
                    families.add("policy_or_parser")
                if "failure" in name or "journal" in name or "report" in name:
                    families.add("failure_journal")
                if "artifact" in name or "quarantine" in name:
                    families.add("artifact_quarantine")
                if "runtime" in name or "snapshot" in name or "worktree" in name or "branch" in name:
                    families.add("runtime_foundations")
                if "spec" in name:
                    families.add("spec_mode")

        if protected_execution_attempted or protected_targets_identified:
            families.add("protected_method_mode")
        if mixed_task:
            # Strong signal that protected and normal edits were mixed.
            families.add("mixed_modes")

        core_like = {
            "orchestrator_cli",
            "orchestrator_core",
            "policy_or_parser",
            "failure_journal",
            "artifact_quarantine",
            "runtime_foundations",
            "spec_mode",
        }
        core_present = families & core_like

        recommend_reasons: list[str] = []
        if len(core_present) >= 2:
            recommend_reasons.append("multiple_orchestrator_seams")
        if "docs" in families and core_present:
            recommend_reasons.append("docs_plus_core")
        if ("protected_method_mode" in families or mixed_task) and (core_present or normal_bundle_attempted):
            recommend_reasons.append("protected_plus_normal")

        # Produce guidance once per run.
        if recommend_reasons and not shell_globals.get("_split_advisory_emitted"):
            fam_list = ", ".join(sorted(families))
            reason_list = ", ".join(sorted(set(recommend_reasons)))
            print("Recommendation: split this task into focused subtasks.")
            print(f"Detected seam families: {fam_list}")
            print(f"Heuristic triggers: {reason_list}")
            print("Proceeding without enforcing a split.")
            shell_globals["_split_advisory_emitted"] = True
    except Exception:
        # Heuristic is best-effort and non-fatal; ignore any issues silently.
        pass
def _call_request_and_parse_bundle_compat(
    shell_globals: dict[str, Any],
    messages: list[dict[str, Any]],
    args: Any,
    last_output_path: Path,
    *,
    forbidden_paths: list[str] | None = None,
    expected_paths: list[str] | None = None,
    baseline: dict[str, str] | None = None,
    task_text: str = "",
    bundle_failure_path: Path | None = None,
) -> dict[str, str]:
    request_bundle = shell_globals["request_and_parse_bundle"]
    try:
        return request_bundle(
            messages,
            args.model,
            args.provider,
            last_output_path,
            forbidden_paths=forbidden_paths,
            expected_paths=expected_paths,
            baseline=baseline,
            task_text=task_text,
            bundle_failure_path=bundle_failure_path,
        )
    except TypeError as exc:
        msg = str(exc)
        if "unexpected keyword argument" not in msg:
            raise
        return request_bundle(
            messages,
            args.model,
            args.provider,
            last_output_path,
            forbidden_paths=forbidden_paths,
            expected_paths=expected_paths,
            baseline=baseline,
        )

def route_shell_main(args: Any, shell_globals: dict[str, Any]) -> int:
    if str(getattr(args, "bootstrap_project", "") or "").strip():
        target_dir = Path(str(args.bootstrap_project).strip())
        bootstrap_exports = shell_globals["_bootstrap_exports"]()
        bootstrap_cfg = bootstrap_exports.get("bootstrap_project_config_scaffold")
        bootstrap_adapter = bootstrap_exports.get("bootstrap_project_adapter_scaffold")
        if not callable(bootstrap_cfg) or not callable(bootstrap_adapter):
            print("❌ Bootstrap unavailable: required scaffold helpers are not importable.")
            return 1
        bootstrap_cfg(target_dir)
        bootstrap_adapter(target_dir)
        print(f"✅ Bootstrapped project scaffold at: {target_dir.as_posix()}")
        return 0

    if not getattr(args, "task", None):
        raise SystemExit("Task file path is required unless --bootstrap-project is used.")

    task_path = Path(args.task)
    if not task_path.exists():
        raise SystemExit(f"Task file not found: {task_path}")

    task_text = task_path.read_text(encoding="utf-8", errors="replace")
    spec_exports = shell_globals["_spec_mode_exports"]()

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

    shell_globals["ensure_clean_worktree"]()

    required = shell_globals["parse_required_files"](task_text)
    require_material_update = shell_globals["task_requires_material_update"](task_text)
    allow_unchanged_cli = shell_globals["task_allows_unchanged_cli"](task_text)
    harness_policies = shell_globals["parse_harness_file_policies"](task_text)
    protected_targets = shell_globals["_extract_protected_method_targets"](task_text)
    protected_method_paths = {str(t["path"]) for t in protected_targets}
    partition = shell_globals.get("_partition_required_paths_for_normal_bundle")
    if callable(partition):
        bundle_required, protected_required = partition(required, protected_method_paths)
    else:
        bundle_required, protected_required = _partition_required_paths_for_normal_bundle(required, protected_method_paths)
    if protected_required and not protected_targets:
        infer_targets = shell_globals.get("_infer_protected_method_targets_from_required")
        if callable(infer_targets):
            protected_targets = infer_targets(task_text, protected_required)
        else:
            protected_targets = _infer_protected_method_targets_from_required(task_text, protected_required)
        protected_method_paths = {str(t["path"]) for t in protected_targets}
        if callable(partition):
            bundle_required, protected_required = partition(required, protected_method_paths)
        else:
            bundle_required, protected_required = _partition_required_paths_for_normal_bundle(required, protected_method_paths)
    protected_target_names = [str(t.get("path", "")).strip().replace("\\", "/") for t in protected_targets if str(t.get("path", "")).strip()]
    protected_bundle_blocked_paths = _normalize_paths(protected_required + protected_target_names)
    baseline_builder = shell_globals.get("_task_baseline_paths")
    if callable(baseline_builder):
        baseline_paths = baseline_builder(required, harness_policies, protected_targets)
    else:
        baseline_paths = sorted(set(required) | set(harness_policies.keys()) | protected_method_paths)

    # Advisory-only task-scope heuristic: detect broad multi-seam tasks early.
    try:
        if not shell_globals.get("_split_advisory_emitted"):
            families: set[str] = set()
            all_paths = _normalize_paths(list(required))
            # Docs/tests
            for p in all_paths:
                lp = p.lower()
                if lp.endswith(".md") or lp.startswith("docs/") or "/docs/" in lp:
                    families.add("docs")
                if lp.startswith("tests/"):
                    families.add("tests")
                if p == "agents/run_task.py":
                    families.add("orchestrator_cli")
                if lp.startswith("agents/lib/"):
                    name = p.split("/")[-1].lower()
                    if "shell_router" in name:
                        families.add("orchestrator_core")
                    if "bundle" in name or "protected" in name or "policy" in name or "parser" in name:
                        families.add("policy_or_parser")
                    if "failure" in name or "journal" in name or "report" in name:
                        families.add("failure_journal")
                    if "artifact" in name or "quarantine" in name:
                        families.add("artifact_quarantine")
                    if "runtime" in name or "snapshot" in name or "worktree" in name or "branch" in name:
                        families.add("runtime_foundations")
                    if "spec" in name:
                        families.add("spec_mode")
            if protected_method_paths:
                families.add("protected_method_mode")

            core_like = {
                "orchestrator_cli",
                "orchestrator_core",
                "policy_or_parser",
                "failure_journal",
                "artifact_quarantine",
                "runtime_foundations",
                "spec_mode",
            }
            core_present = families & core_like

            recommend_reasons: list[str] = []
            if len(core_present) >= 2:
                recommend_reasons.append("multiple_orchestrator_seams")
            if "docs" in families and core_present:
                recommend_reasons.append("docs_plus_core")
            if "protected_method_mode" in families and (core_present or ("docs" in families)) and (bool(bundle_required) and bool(protected_required or protected_targets)):
                recommend_reasons.append("protected_plus_normal")

            if recommend_reasons:
                fam_list = ", ".join(sorted(families))
                reason_list = ", ".join(sorted(set(recommend_reasons)))
                print("Recommendation: split this task into focused subtasks.")
                print(f"Detected seam families: {fam_list}")
                print(f"Heuristic triggers: {reason_list}")
                print("Proceeding without enforcing a split.")
                shell_globals["_split_advisory_emitted"] = True
    except Exception:
        # Non-fatal heuristic best-effort.
        pass

    branch = shell_globals["_choose_agent_branch"](task_path.stem, args.push)
    print(f"Current branch: {shell_globals['capture'](['git', 'rev-parse', '--abbrev-ref', 'HEAD'])}")
    print(f"Creating branch: {branch}")
    if branch != f"agent-{task_path.stem}":
        print("Branch name was auto-suffixed to avoid stale local/remote branch conflicts.")
    print(f"Using provider: {args.provider}")
    print(f"Using model: {args.model}")
    shell_globals["ensure_branch"](branch)

    last_output_path = Path("_last_agent_model_output.txt")
    last_bundle_path = Path("_last_agent_file_bundle.txt")

    prev_files: dict[str, str] | None = None
    extra_directives = ""
    violation_counts: dict[str, int] = {}

    stable_baseline = shell_globals["existing_file_contents"](baseline_paths)

    for it in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {it}/{args.max_iters} ===")
        baseline = shell_globals["existing_file_contents"](baseline_paths)
        for protected_path in protected_method_paths:
            if protected_path in stable_baseline:
                baseline[protected_path] = stable_baseline[protected_path]
            else:
                baseline.pop(protected_path, None)

        files: dict[str, str] = {}
        try:
            if protected_required and not protected_targets and not bundle_required:
                reason = "Explicit protected deliverables require protected method mode or manual patch: " + ", ".join(protected_required)
                shell_globals["_report_failure"]("bundle_transport", reason)
                _emit_failure_artifact_messages(shell_globals, last_output_path, last_bundle_path, task_file=task_path.as_posix(), failure_category="bundle_transport", protected_files=protected_required, before_model_output=True, normal_bundle_attempted=False, reason=reason, protected_execution_attempted=False, mixed_task=False, protected_targets_identified=protected_target_names)
                return 1
            for target in protected_targets:
                target_path = str(target["path"])
                mode = str(target["mode"])
                method_name = str(target["method_name"])
                original_baseline_content = baseline.get(target_path)
                if original_baseline_content is None:
                    raise shell_globals["FileBundleError"](
                        f"Protected method target `{target_path}` has no baseline content."
                    )
                working_content = files.get(target_path, original_baseline_content)
                anchor = str(target.get("anchor", "")) if mode == "append" else ""
                insertion_messages = shell_globals["build_method_insertion_messages"](
                    task_text,
                    target_path,
                    method_name,
                    working_content,
                    mode,
                    extra_directives,
                    anchor=anchor,
                )
                method_text = shell_globals["request_and_parse_method_insertion"](
                    insertion_messages,
                    args.model,
                    args.provider,
                    last_output_path,
                    target_path,
                    method_name,
                )
                if mode == "append":
                    files[target_path] = shell_globals["apply_method_insertion"](
                        working_content,
                        anchor,
                        method_name,
                        method_text,
                    )
                else:
                    files[target_path] = shell_globals["apply_method_replacement"](
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
                virtual_context = {p: files[p] for p in protected_bundle_blocked_paths if p in files}
                messages = shell_globals["build_messages"](
                    task_text,
                    bundle_required,
                    non_protected_directives,
                    virtual_context=virtual_context,
                    forbidden_normal_bundle_paths=protected_bundle_blocked_paths,
                )
                generated = _call_request_and_parse_bundle_compat(
                    shell_globals,
                    messages,
                    args,
                    last_output_path,
                    forbidden_paths=protected_bundle_blocked_paths,
                    expected_paths=bundle_required,
                    baseline=baseline,
                    task_text=task_text,
                    bundle_failure_path=last_bundle_path,
                )
                files.update(generated)
            elif not files:
                virtual_context = {p: files[p] for p in protected_bundle_blocked_paths if p in files}
                messages = shell_globals["build_messages"](
                    task_text,
                    required,
                    extra_directives,
                    virtual_context=virtual_context,
                    forbidden_normal_bundle_paths=protected_bundle_blocked_paths,
                )
                files = _call_request_and_parse_bundle_compat(
                    shell_globals,
                    messages,
                    args,
                    last_output_path,
                    forbidden_paths=protected_bundle_blocked_paths,
                    expected_paths=required,
                    baseline=baseline,
                    task_text=task_text,
                    bundle_failure_path=last_bundle_path,
                )
        except shell_globals["FileBundleError"] as e:
            shell_globals["_report_failure"]("bundle_transport", str(e))
            _emit_failure_artifact_messages(shell_globals, last_output_path, last_bundle_path, task_file=task_path.as_posix(), failure_category="bundle_transport", protected_files=protected_bundle_blocked_paths, before_model_output=not last_output_path.exists(), normal_bundle_attempted=bool(bundle_required), reason=str(e), protected_execution_attempted=bool(protected_targets), mixed_task=bool(bundle_required and protected_bundle_blocked_paths), protected_targets_identified=protected_target_names)
            return 1

        pretty: list[str] = [shell_globals["FILE_BUNDLE_BEGIN"]]
        for p, c in files.items():
            pretty.append(f"FILE: {p}")
            pretty.append(c.rstrip("\n"))
            pretty.append(shell_globals["FILE_END"])
        pretty.append(shell_globals["FILE_BUNDLE_END"])
        last_bundle_path.write_text("\n".join(pretty) + "\n", encoding="utf-8", newline="\n")

        ok_syntax, syntax_msg = shell_globals["validate_python_syntax"](files)
        if not ok_syntax:
            shell_globals["_report_failure"]("python_syntax", syntax_msg)
            task_text = shell_globals["_append_task_feedback"](task_text, syntax_msg)
            if shell_globals["_repeat_limit_exceeded"](violation_counts, "python_syntax", args.policy_block_limit):
                print("\n❌ Stopping early: repeated Python syntax failures. Recommended action: manual_patch")
                _emit_failure_artifact_messages(shell_globals, last_output_path, last_bundle_path, task_file=task_path.as_posix(), failure_category="policy_block", protected_files=protected_bundle_blocked_paths, before_model_output=not last_output_path.exists(), normal_bundle_attempted=bool(bundle_required), reason="Repeated policy or validation failure", protected_execution_attempted=bool(protected_targets), mixed_task=bool(bundle_required and protected_bundle_blocked_paths), protected_targets_identified=protected_target_names)
                return 1
            prev_files = files
            continue

        ok_req, req_msg = shell_globals["enforce_required_files"](
            required,
            files,
            baseline,
            require_material_update=require_material_update,
            allow_unchanged_cli=allow_unchanged_cli,
        )
        if not ok_req:
            shell_globals["_report_failure"]("deliverables", req_msg)
            task_text = shell_globals["_append_task_feedback"](task_text, req_msg)
            if shell_globals["_repeat_limit_exceeded"](violation_counts, "deliverables", args.policy_block_limit):
                print("\n❌ Stopping early: repeated deliverable violations. Recommended action: manual_patch")
                _emit_failure_artifact_messages(shell_globals, last_output_path, last_bundle_path, task_file=task_path.as_posix(), failure_category="policy_block", protected_files=protected_bundle_blocked_paths, before_model_output=not last_output_path.exists(), normal_bundle_attempted=bool(bundle_required), reason="Repeated policy or validation failure", protected_execution_attempted=bool(protected_targets), mixed_task=bool(bundle_required and protected_bundle_blocked_paths), protected_targets_identified=protected_target_names)
                return 1
            prev_files = files
            continue

        ok_policy, policy_msg = shell_globals["enforce_harness_file_policies"](task_text, files, baseline)
        if not ok_policy:
            shell_globals["_report_failure"]("protected_file_policy", policy_msg)
            task_text = shell_globals["_append_task_feedback"](task_text, policy_msg)
            if shell_globals["_repeat_limit_exceeded"](violation_counts, "protected_file_policy", args.policy_block_limit):
                print("\n❌ Stopping early: repeated protected-file policy violations. Recommended action: manual_patch")
                _emit_failure_artifact_messages(shell_globals, last_output_path, last_bundle_path, task_file=task_path.as_posix(), failure_category="policy_block", protected_files=protected_bundle_blocked_paths, before_model_output=not last_output_path.exists(), normal_bundle_attempted=bool(bundle_required), reason="Repeated policy or validation failure", protected_execution_attempted=bool(protected_targets), mixed_task=bool(bundle_required and protected_bundle_blocked_paths), protected_targets_identified=protected_target_names)
                return 1
            prev_files = files
            continue

        ok_static, static_msg = shell_globals["validate_static_bundle_contracts"](files, task_text)
        if not ok_static:
            shell_globals["_report_failure"]("static_contracts", static_msg)
            task_text = shell_globals["_append_task_feedback"](task_text, static_msg)
            if shell_globals["_repeat_limit_exceeded"](violation_counts, "static_contracts", args.policy_block_limit):
                print("\n❌ Stopping early: repeated static contract violations. Recommended action: manual_patch")
                _emit_failure_artifact_messages(shell_globals, last_output_path, last_bundle_path, task_file=task_path.as_posix(), failure_category="policy_block", protected_files=protected_bundle_blocked_paths, before_model_output=not last_output_path.exists(), normal_bundle_attempted=bool(bundle_required), reason="Repeated policy or validation failure", protected_execution_attempted=bool(protected_targets), mixed_task=bool(bundle_required and protected_bundle_blocked_paths), protected_targets_identified=protected_target_names)
                return 1
            prev_files = files
            continue

        ok_imports, import_msg = shell_globals["validate_imports"](files)
        if not ok_imports:
            shell_globals["_report_failure"]("imports", import_msg)
            task_text = shell_globals["_append_task_feedback"](
                task_text, import_msg + "\n" + shell_globals["missing_module_hints"](import_msg)
            )
            if shell_globals["_repeat_limit_exceeded"](violation_counts, "imports", args.policy_block_limit):
                print("\n❌ Stopping early: repeated import validation failures. Recommended action: manual_patch")
                _emit_failure_artifact_messages(shell_globals, last_output_path, last_bundle_path, task_file=task_path.as_posix(), failure_category="policy_block", protected_files=protected_bundle_blocked_paths, before_model_output=not last_output_path.exists(), normal_bundle_attempted=bool(bundle_required), reason="Repeated policy or validation failure", protected_execution_attempted=bool(protected_targets), mixed_task=bool(bundle_required and protected_bundle_blocked_paths), protected_targets_identified=protected_target_names)
                return 1
            prev_files = files
            continue

        pre_write_snapshot = shell_globals["snapshot_file_contents"](list(files.keys()))
        shell_globals["write_files"](files)
        violation_counts.clear()

        ok, details = shell_globals["run_checks"]()
        if ok:
            print("✅ Green.")
            if args.push:
                shell_globals["_cleanup_runtime_artifacts_for_commit"](
                    shell_globals["_runtime_artifact_paths"](last_output_path, last_bundle_path)
                )
                shell_globals["run"](["git", "add", "-A"], check=True)
                staged = shell_globals["capture"](["git", "diff", "--cached", "--name-only"])
                if not staged.strip():
                    print("✅ Green. No changes to commit/push.")
                    return 0
                shell_globals["run"](["git", "commit", "-m", f"{task_path.stem}: apply agent changes"], check=True)
                shell_globals["run"](["git", "push", "-u", "origin", branch], check=True)
                print(f"Pushed branch: {branch}")
                print("Create a PR on GitHub for this branch (repo rules require PR).")
            return 0

        shell_globals["restore_file_snapshot"](pre_write_snapshot)

        print("❌ Checks failed after applying changes:")
        print(details)

        semantic_hints = shell_globals["parse_semantic_failures"](details)
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
            sim = shell_globals["bundle_similarity"](prev_files, files)
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
