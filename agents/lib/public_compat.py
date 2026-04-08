from __future__ import annotations

from typing import Any, Iterable, Mapping

COMPATIBILITY_CONTRACT_VERSION = 1

FAILURE_RECORD_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "failure_kind": ("failure_kind", "kind"),
    "failure_message": ("failure_message", "message"),
    "failure_category": ("failure_category", "category"),
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
        "failure_record_field_aliases": {k: list(v) for k, v in FAILURE_RECORD_FIELD_ALIASES.items()},
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


def coerce_failure_record_fields(payload: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, str]:
    src = dict(payload or {})
    src.update(overrides)
    return {
        canonical: str(first_present(src, aliases, "") or "").strip()
        for canonical, aliases in FAILURE_RECORD_FIELD_ALIASES.items()
    }


def coerce_manifest_entry_path(entry: Mapping[str, Any] | None = None) -> str:
    return str(first_present(entry, MANIFEST_ENTRY_PATH_ALIASES, "") or "").strip().replace("\\", "/")


def apply_project_contract_convenience_keys(contract: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, object]:
    result = dict(contract or {})
    result.update(overrides)
    for canonical, aliases in PROJECT_CONVENIENCE_KEYS.items():
        value = first_present(result, aliases, result.get(canonical, ""))
        if canonical == "carry_forward_memory_namespace" and value in (None, ""):
            project_id = str(result.get("project_id", "") or "")
            value = f"carry_forward/{project_id}" if project_id else "carry_forward/ambiguous_project"
        result[canonical] = str(value or "")
        for alias in aliases:
            result[alias] = str(value or "")
    return result


def canonical_manual_patch_batch_status(status: str) -> str:
    text = str(status or "").strip()
    if text in MANUAL_PATCH_BATCH_STATUSES:
        return "manual_patch_required"
    return text
