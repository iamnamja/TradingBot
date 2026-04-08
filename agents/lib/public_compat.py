from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

COMPATIBILITY_CONTRACT_VERSION = 2
SCHEMA_ALIAS_NORMALIZATION_ENABLED = True

FAILURE_RECORD_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "failure_kind": ("failure_kind", "kind"),
    "failure_message": ("failure_message", "message"),
    "failure_category": ("failure_category", "category"),
}

FAILURE_REMEDIATION_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "retry_count": ("retry_count",),
    "max_repair_attempts": ("max_repair_attempts", "repair_attempt_budget"),
}

MANIFEST_ENTRY_PATH_ALIASES: tuple[str, ...] = ("path", "task_path", "task")

PROJECT_CONVENIENCE_KEYS: dict[str, tuple[str, ...]] = {
    "workspace_root": ("workspace_root", "project_workspace_root"),
    "branch_namespace": ("branch_namespace", "project_branch_namespace"),
    "state_namespace": ("state_namespace", "project_state_namespace"),
    "checkpoint_namespace": ("checkpoint_namespace", "project_checkpoint_namespace"),
    "carry_forward_memory_namespace": ("carry_forward_memory_namespace",),
}

MANUAL_PATCH_BATCH_STATUSES = {"manual_patch", "manual_patch_required"}


def compatibility_contract_snapshot() -> dict[str, object]:
    return {
        "contract_version": COMPATIBILITY_CONTRACT_VERSION,
        "schema_alias_normalization_enabled": SCHEMA_ALIAS_NORMALIZATION_ENABLED,
        "failure_record_field_aliases": {k: list(v) for k, v in FAILURE_RECORD_FIELD_ALIASES.items()},
        "failure_remediation_field_aliases": {k: list(v) for k, v in FAILURE_REMEDIATION_FIELD_ALIASES.items()},
        "manifest_entry_path_aliases": list(MANIFEST_ENTRY_PATH_ALIASES),
        "project_convenience_keys": {k: list(v) for k, v in PROJECT_CONVENIENCE_KEYS.items()},
        "manual_patch_batch_statuses": sorted(MANUAL_PATCH_BATCH_STATUSES),
        "public_compatibility_frozen": True,
    }


def first_present(mapping: Mapping[str, Any] | None, keys: Iterable[str], default: Any = "") -> Any:
    src = dict(mapping or {})
    for key in keys:
        if key in src and src[key] not in (None, ""):
            return src[key]
    return default


def _normalized_path_value(raw: object) -> str:
    return str(raw or "").strip().replace("\\", "/")


def _normalize_int(raw: object, default: int = 0) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return int(default)


def _normalize_bool(raw: object, default: bool = False) -> bool:
    if isinstance(raw, bool):
        return raw
    if raw in (None, ""):
        return default
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False
    return bool(raw)


def _normalize_path_list(value: object, *, error_message: str) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError(error_message)
    result: list[str] = []
    for item in value:
        path = _normalized_path_value(item)
        if path and path not in result:
            result.append(path)
    return result


def normalize_failure_record_payload(payload: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, str]:
    src = dict(payload or {})
    src.update(overrides)
    return {
        canonical: str(first_present(src, aliases, "") or "").strip()
        for canonical, aliases in FAILURE_RECORD_FIELD_ALIASES.items()
    }


def coerce_failure_record_fields(payload: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, str]:
    return normalize_failure_record_payload(payload, **overrides)


def normalize_failure_remediation_payload(payload: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, object]:
    src = dict(payload or {})
    src.update(overrides)
    record = normalize_failure_record_payload(src)
    retry_count = max(0, _normalize_int(first_present(src, FAILURE_REMEDIATION_FIELD_ALIASES["retry_count"], 0), 0))

    raw_budget = src.get("repair_attempt_budget", None)
    if raw_budget not in (None, ""):
        max_attempts = max(1, _normalize_int(raw_budget, 3))
    else:
        max_attempts = max(1, _normalize_int(first_present(src, FAILURE_REMEDIATION_FIELD_ALIASES["max_repair_attempts"], 3), 3))

    return {
        **record,
        "retry_count": retry_count,
        "max_repair_attempts": max_attempts,
        "repair_attempt_budget": max_attempts,
    }


def coerce_manifest_entry_path(entry: Mapping[str, Any] | None = None) -> str:
    return str(first_present(entry, MANIFEST_ENTRY_PATH_ALIASES, "") or "").strip().replace("\\", "/")


def normalize_manifest_entry_payload(entry: Any, *, index: int = 0) -> dict[str, object]:
    if isinstance(entry, str):
        task_path = _normalized_path_value(entry)
        if not task_path:
            raise ValueError(f"Manifest entry at index {index} is empty.")
        task_id = Path(task_path).stem or f"task_{index+1}"
        return {
            "task_id": task_id,
            "path": task_path,
            "task_path": task_path,
            "task": task_path,
            "label": "",
            "note": "",
            "stop_policy": "",
            "depends_on": [],
            "blocks": [],
            "deferrable": False,
            "skipped_by_policy": False,
            "rerun_required": False,
        }
    if not isinstance(entry, Mapping):
        raise ValueError(f"Manifest entry at index {index} must be a string or mapping.")
    task_path = _normalized_path_value(coerce_manifest_entry_path(entry))
    if not task_path:
        raise ValueError(f"Manifest entry at index {index} is missing `path` or `task_path`.")
    task_id = str(entry.get("task_id") or Path(task_path).stem or f"task_{index+1}").strip()
    return {
        "task_id": task_id,
        "path": task_path,
        "task_path": task_path,
        "task": task_path,
        "label": str(entry.get("label") or "").strip(),
        "note": str(entry.get("note") or "").strip(),
        "stop_policy": str(entry.get("stop_policy") or "").strip(),
        "depends_on": _normalize_path_list(entry.get("depends_on"), error_message=f"Manifest entry at index {index} dependency field must be a list."),
        "blocks": _normalize_path_list(entry.get("blocks"), error_message=f"Manifest entry at index {index} dependency field must be a list."),
        "deferrable": _normalize_bool(entry.get("deferrable", entry.get("optional", False))),
        "skipped_by_policy": _normalize_bool(entry.get("skipped_by_policy", entry.get("skip_by_policy", False))),
        "rerun_required": _normalize_bool(entry.get("rerun_required", False)),
    }


def normalize_manifest_entries_payload(task_manifest: Mapping[str, Any] | Sequence[Any]) -> list[dict[str, object]]:
    raw_tasks = task_manifest.get("tasks", []) if isinstance(task_manifest, Mapping) else task_manifest
    return [normalize_manifest_entry_payload(raw, index=i) for i, raw in enumerate(raw_tasks)]


def normalize_project_contract_payload(contract: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, object]:
    result = dict(contract or {})
    result.update(overrides)
    project_id = str(result.get("project_id", "") or "").strip()
    workspace_root = _normalized_path_value(first_present(result, PROJECT_CONVENIENCE_KEYS["workspace_root"], result.get("repo_root", ".")) or ".") or "."
    if workspace_root in {"", "./"}:
        workspace_root = "."
    repo_root = _normalized_path_value(result.get("project_repo_root", result.get("repo_root", workspace_root)) or workspace_root) or workspace_root
    branch_namespace = str(first_present(result, PROJECT_CONVENIENCE_KEYS["branch_namespace"], f"project/{project_id}" if project_id else "project/ambiguous_project") or "").strip()
    state_namespace = str(first_present(result, PROJECT_CONVENIENCE_KEYS["state_namespace"], f"state/{project_id}" if project_id else "state/ambiguous_project") or "").strip()
    checkpoint_namespace = str(first_present(result, PROJECT_CONVENIENCE_KEYS["checkpoint_namespace"], f"checkpoint/{project_id}" if project_id else "checkpoint/ambiguous_project") or "").strip()
    carry_forward_memory_namespace = str(first_present(result, PROJECT_CONVENIENCE_KEYS["carry_forward_memory_namespace"], f"carry_forward/{project_id}" if project_id else "carry_forward/ambiguous_project") or "").strip()
    normalized = dict(result)
    normalized.update(
        {
            "project_id": project_id,
            "workspace_root": workspace_root,
            "project_workspace_root": workspace_root,
            "repo_root": repo_root,
            "project_repo_root": repo_root,
            "branch_namespace": branch_namespace,
            "project_branch_namespace": branch_namespace,
            "state_namespace": state_namespace,
            "project_state_namespace": state_namespace,
            "checkpoint_namespace": checkpoint_namespace,
            "project_checkpoint_namespace": checkpoint_namespace,
            "carry_forward_memory_namespace": carry_forward_memory_namespace,
        }
    )
    return normalized


def apply_project_contract_convenience_keys(contract: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, object]:
    return normalize_project_contract_payload(contract, **overrides)


def canonical_manual_patch_batch_status(status: str) -> str:
    text = str(status or "").strip()
    if text in MANUAL_PATCH_BATCH_STATUSES:
        return "manual_patch_required"
    return text
