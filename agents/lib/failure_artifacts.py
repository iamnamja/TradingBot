from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def build_placeholder_payload(
    *,
    artifact_kind: str,
    task_file: str = "",
    failure_category: str = "",
    protected_files: list[str] | None = None,
    before_model_output: bool = False,
    normal_bundle_attempted: bool = False,
    reason: str = "",
    protected_execution_attempted: bool = False,
    mixed_task: bool = False,
    protected_targets_identified: list[str] | None = None,
) -> dict[str, object]:
    return {
        "placeholder": True,
        "artifact_kind": artifact_kind,
        "status": "unavailable",
        "reason": reason or "failure occurred before artifact content was produced",
        "task_file": Path(task_file).as_posix() if task_file else "",
        "failure_category": failure_category,
        "protected_files": list(protected_files or []),
        "before_model_output": bool(before_model_output),
        "normal_bundle_attempted": bool(normal_bundle_attempted),
        "protected_execution_attempted": bool(protected_execution_attempted),
        "mixed_task": bool(mixed_task),
        "protected_targets_identified": list(protected_targets_identified or []),
    }


def write_json_artifact(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def ensure_truthful_failure_artifacts(
    *,
    last_output_path: Path,
    last_bundle_path: Path,
    create_placeholders: bool = False,
    task_file: str = "",
    failure_category: str = "",
    protected_files: list[str] | None = None,
    before_model_output: bool = False,
    normal_bundle_attempted: bool = False,
    reason: str = "",
    protected_execution_attempted: bool = False,
    mixed_task: bool = False,
    protected_targets_identified: list[str] | None = None,
) -> None:
    should_create = bool(create_placeholders or before_model_output)
    if should_create and not last_output_path.exists():
        write_json_artifact(
            last_output_path,
            build_placeholder_payload(
                artifact_kind="model_output_placeholder",
                task_file=task_file,
                failure_category=failure_category,
                protected_files=protected_files,
                before_model_output=before_model_output,
                normal_bundle_attempted=normal_bundle_attempted,
                reason=reason,
                protected_execution_attempted=protected_execution_attempted,
                mixed_task=mixed_task,
                protected_targets_identified=protected_targets_identified,
            ),
        )
    if should_create and not last_bundle_path.exists():
        payload = build_placeholder_payload(
            artifact_kind="file_bundle_placeholder",
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
        payload["kind"] = "file_bundle"
        payload["files"] = []
        write_json_artifact(last_bundle_path, payload)


def format_failure_artifact_messages(last_output_path: Path, last_bundle_path: Path) -> list[str]:
    lines: list[str] = []
    if last_output_path.exists():
        lines.append(f"Model output saved to: {last_output_path}")
    else:
        lines.append(f"Model output was not written: {last_output_path}")
    if last_bundle_path.exists():
        lines.append(f"Parsed file bundle saved to: {last_bundle_path}")
    else:
        lines.append(f"Parsed file bundle was not written: {last_bundle_path}")
    return lines


def emit_failure_artifact_messages(**kwargs: Any) -> None:
    shell_globals = kwargs.pop("shell_globals", None)
    last_output_path = Path(kwargs["last_output_path"])
    last_bundle_path = Path(kwargs["last_bundle_path"])

    ensure_truthful_failure_artifacts(
        last_output_path=last_output_path,
        last_bundle_path=last_bundle_path,
        create_placeholders=bool(kwargs.get("create_placeholders", False)),
        task_file=str(kwargs.get("task_file", "") or ""),
        failure_category=str(kwargs.get("failure_category", "") or ""),
        protected_files=list(kwargs.get("protected_files", []) or []),
        before_model_output=bool(kwargs.get("before_model_output", False)),
        normal_bundle_attempted=bool(kwargs.get("normal_bundle_attempted", False)),
        reason=str(kwargs.get("reason", "") or ""),
        protected_execution_attempted=bool(kwargs.get("protected_execution_attempted", False)),
        mixed_task=bool(kwargs.get("mixed_task", False)),
        protected_targets_identified=list(kwargs.get("protected_targets_identified", []) or []),
    )

    for line in format_failure_artifact_messages(last_output_path, last_bundle_path):
        print(line)

    _ = shell_globals
