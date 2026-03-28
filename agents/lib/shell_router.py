from __future__ import annotations

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
        text = str(exc)
        unsupported_task_text = "unexpected keyword argument 'task_text'" in text
        unsupported_bundle_failure = "unexpected keyword argument 'bundle_failure_path'" in text
        if not (unsupported_task_text or unsupported_bundle_failure):
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
    baseline_paths = sorted(set(required) | set(harness_policies.keys()))
    protected_targets = shell_globals["_extract_protected_method_targets"](task_text)
    protected_method_paths = {str(t["path"]) for t in protected_targets}

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
        bundle_required = [p for p in required if p not in protected_method_paths]

        files: dict[str, str] = {}
        try:
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
                virtual_context = {p: files[p] for p in sorted(protected_method_paths) if p in files}
                messages = shell_globals["build_messages"](
                    task_text,
                    bundle_required,
                    non_protected_directives,
                    virtual_context=virtual_context,
                    forbidden_normal_bundle_paths=sorted(protected_method_paths),
                )
                generated = shell_globals["request_and_parse_bundle"](
                    messages,
                    args.model,
                    args.provider,
                    last_output_path,
                    forbidden_paths=sorted(protected_method_paths),
                    expected_paths=bundle_required,
                    baseline=baseline,
                )
                files.update(generated)
            elif not files:
                virtual_context = {p: files[p] for p in sorted(protected_method_paths) if p in files}
                messages = shell_globals["build_messages"](
                    task_text,
                    required,
                    extra_directives,
                    virtual_context=virtual_context,
                    forbidden_normal_bundle_paths=sorted(protected_method_paths),
                )
                files = shell_globals["request_and_parse_bundle"](
                    messages,
                    args.model,
                    args.provider,
                    last_output_path,
                    forbidden_paths=sorted(protected_method_paths),
                    expected_paths=required,
                    baseline=baseline,
                )
        except shell_globals["FileBundleError"] as e:
            shell_globals["_report_failure"]("bundle_transport", str(e))
            print(f"Model output saved to: {last_output_path}")
            print(f"Parsed file bundle saved to: {last_bundle_path}")
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
                print("Model output saved to: _last_agent_model_output.txt")
                print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
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
                print("Model output saved to: _last_agent_model_output.txt")
                print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
                return 1
            prev_files = files
            continue

        ok_policy, policy_msg = shell_globals["enforce_harness_file_policies"](task_text, files, baseline)
        if not ok_policy:
            shell_globals["_report_failure"]("protected_file_policy", policy_msg)
            task_text = shell_globals["_append_task_feedback"](task_text, policy_msg)
            if shell_globals["_repeat_limit_exceeded"](violation_counts, "protected_file_policy", args.policy_block_limit):
                print("\n❌ Stopping early: repeated protected-file policy violations. Recommended action: manual_patch")
                print("Model output saved to: _last_agent_model_output.txt")
                print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
                return 1
            prev_files = files
            continue

        ok_static, static_msg = shell_globals["validate_static_bundle_contracts"](files, task_text)
        if not ok_static:
            shell_globals["_report_failure"]("static_contracts", static_msg)
            task_text = shell_globals["_append_task_feedback"](task_text, static_msg)
            if shell_globals["_repeat_limit_exceeded"](violation_counts, "static_contracts", args.policy_block_limit):
                print("\n❌ Stopping early: repeated static contract violations. Recommended action: manual_patch")
                print("Model output saved to: _last_agent_model_output.txt")
                print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
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
                print("Model output saved to: _last_agent_model_output.txt")
                print("Parsed file bundle saved to: _last_agent_file_bundle.txt")
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
