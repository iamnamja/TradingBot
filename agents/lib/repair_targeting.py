from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence


class FailureFamily(Enum):
    ADMISSION_MISSING_DELIVERABLE = "admission_missing_deliverable"
    IMPORT_PUBLIC_COMPAT_FAILURE = "import_public_compat_failure"
    ARTIFACT_PATH_MISMATCH = "artifact_path_mismatch"
    ARTIFACT_SHAPE_MISMATCH = "artifact_shape_mismatch"
    BENCHMARK_COMPAT_REGRESSION = "benchmark_compat_regression"
    STATIC_PROTECTED_VIOLATION = "static_protected_violation"
    RESUME_REENTRY_MISMATCH = "resume_reentry_mismatch"
    GENERIC = "generic"

    @property
    def short_code(self) -> str:
        return self.value


@dataclass(frozen=True)
class RepairTarget:
    name: str
    allowed_paths: Sequence[str] = field(default_factory=tuple)
    protected: bool = False
    notes: str = ""


@dataclass(frozen=True)
class ClassificationRecord:
    family: FailureFamily
    short_code: str
    timestamp: str
    evidence_tags: Sequence[str] = field(default_factory=tuple)

    def to_json(self) -> Mapping[str, Any]:
        return {
            "family": self.family.value,
            "short_code": self.short_code,
            "timestamp": self.timestamp,
            "evidence_tags": list(self.evidence_tags),
        }

    @staticmethod
    def from_json(data: Mapping[str, Any]) -> "ClassificationRecord":
        family = FailureFamily(data["family"]) if isinstance(data["family"], str) else FailureFamily(data["family"]["value"])  # type: ignore[index]
        return ClassificationRecord(
            family=family,
            short_code=data["short_code"],
            timestamp=data["timestamp"],
            evidence_tags=tuple(data.get("evidence_tags", [])),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_failure_family(evidence: Mapping[str, Any]) -> FailureFamily:
    # Strong keyed hints first
    if evidence.get("missing_deliverables") or evidence.get("admission_failure"):
        return FailureFamily.ADMISSION_MISSING_DELIVERABLE

    if evidence.get("benchmark_regression") or evidence.get("benchmark_compat_regression"):
        return FailureFamily.BENCHMARK_COMPAT_REGRESSION

    if evidence.get("protected_surface_violation") or evidence.get("static_contract_violation"):
        return FailureFamily.STATIC_PROTECTED_VIOLATION

    if evidence.get("resume_mismatch") or evidence.get("reentry_mismatch"):
        return FailureFamily.RESUME_REENTRY_MISMATCH

    if evidence.get("artifact_mismatch") == "path":
        return FailureFamily.ARTIFACT_PATH_MISMATCH

    if evidence.get("artifact_mismatch") == "shape" or evidence.get("schema_mismatch"):
        return FailureFamily.ARTIFACT_SHAPE_MISMATCH

    # Message or error-type cues
    message = (evidence.get("message") or "").lower()
    error_type = (evidence.get("error_type") or "").lower()

    if "cannot import" in message or "importerror" in error_type or "module not found" in message:
        return FailureFamily.IMPORT_PUBLIC_COMPAT_FAILURE

    if "attributeerror" in error_type and ("no attribute" in message or "public surface" in message):
        return FailureFamily.IMPORT_PUBLIC_COMPAT_FAILURE

    if "artifact" in message and ("missing" in message or "not found" in message or "path" in message):
        return FailureFamily.ARTIFACT_PATH_MISMATCH

    if "artifact" in message and ("schema" in message or "shape" in message or "keyerror" in message):
        return FailureFamily.ARTIFACT_SHAPE_MISMATCH

    if "benchmark" in message and ("regression" in message or "compat" in message):
        return FailureFamily.BENCHMARK_COMPAT_REGRESSION

    if "protected" in message or "static contract" in message:
        return FailureFamily.STATIC_PROTECTED_VIOLATION

    if "resume" in message or "checkpoint" in message or "re-entry" in message or "reentry" in message:
        return FailureFamily.RESUME_REENTRY_MISMATCH

    # Fallback
    return FailureFamily.GENERIC


def select_repair_targets(family: FailureFamily) -> Sequence[RepairTarget]:
    # Conservative, narrow defaults intended to be further filtered by protected-surface policies.
    if family is FailureFamily.ADMISSION_MISSING_DELIVERABLE:
        return (
            RepairTarget(
                name="deliverables_only",
                allowed_paths=("tasks/", "README.md", "docs/"),
                notes="Satisfy exact deliverable contract; do not broaden runtime changes.",
            ),
        )

    if family is FailureFamily.IMPORT_PUBLIC_COMPAT_FAILURE:
        return (
            RepairTarget(
                name="public_surface_only",
                allowed_paths=("src/**/__init__.py", "src/**/types.py", "agents/lib/public_compat.py"),
                notes="Add non-breaking import aliases or restore frozen symbols; no broad refactors.",
            ),
        )

    if family is FailureFamily.ARTIFACT_PATH_MISMATCH:
        return (
            RepairTarget(
                name="artifact_paths_only",
                allowed_paths=("src/builder/orchestrator/**", "agents/lib/artifact_quarantine.py", "docs/"),
                notes="Correct artifact locations or path joins; avoid changing artifact content shape.",
            ),
        )

    if family is FailureFamily.ARTIFACT_SHAPE_MISMATCH:
        return (
            RepairTarget(
                name="artifact_schema_only",
                allowed_paths=("src/builder/orchestrator/**", "agents/lib/**", "docs/"),
                notes="Normalize result schemas and adapters; do not widen or relocate artifacts.",
            ),
        )

    if family is FailureFamily.BENCHMARK_COMPAT_REGRESSION:
        return (
            RepairTarget(
                name="benchmark_harness_only",
                allowed_paths=("src/builder/orchestrator/benchmark*.py", "src/builder/orchestrator/bounded_corpus_benchmark.py"),
                notes="Patch benchmark adapters and tolerances; avoid touching production bot strategy/runtime.",
            ),
        )

    if family is FailureFamily.STATIC_PROTECTED_VIOLATION:
        return (
            RepairTarget(
                name="compat_alias_or_revert",
                allowed_paths=("src/**/__init__.py", "src/**/types.py", "agents/lib/public_compat.py"),
                notes="Introduce shims/aliases or minimal reverts to satisfy frozen static/protected contracts.",
                protected=True,
            ),
        )

    if family is FailureFamily.RESUME_REENTRY_MISMATCH:
        return (
            RepairTarget(
                name="resume_state_only",
                allowed_paths=("src/builder/orchestrator/state.py", "src/builder/orchestrator/backlog_state.py", "agents/lib/batch_state.py"),
                notes="Fix checkpoint load/save, idempotent re-entry, and environment seams; no broader changes.",
            ),
        )

    # Generic conservative default
    return (
        RepairTarget(
            name="minimal_touch_safe_default",
            allowed_paths=("agents/lib/**",),
            notes="Default to planner/harness shims; avoid touching protected or public production surfaces.",
        ),
    )


def persist_classification(run_dir: Path, family: FailureFamily, evidence: Mapping[str, Any] | None = None) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    record = ClassificationRecord(
        family=family,
        short_code=family.short_code,
        timestamp=_now_iso(),
        evidence_tags=_extract_evidence_tags(evidence or {}),
    )
    # File name includes short code for deterministic dashboards; single latest file per run+family.
    dest = run_dir / f"classification_{family.short_code}.json"
    with dest.open("w", encoding="utf-8") as f:
        json.dump(record.to_json(), f, indent=2, sort_keys=True)
    return dest


def load_recent_classifications(run_dir: Path) -> Sequence[ClassificationRecord]:
    if not run_dir.exists():
        return ()
    records: list[ClassificationRecord] = []
    for path in sorted(run_dir.glob("classification_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            records.append(ClassificationRecord.from_json(data))
        except Exception:
            # Be conservative: skip corrupted files silently, do not raise in orchestrator path.
            continue
    # Sorted by timestamp descending for convenience
    records.sort(key=lambda r: r.timestamp, reverse=True)
    return tuple(records)


def plan_repair_from_evidence(evidence: Mapping[str, Any]) -> tuple[FailureFamily, Sequence[RepairTarget]]:
    family = classify_failure_family(evidence)
    targets = select_repair_targets(family)
    return family, targets


def _extract_evidence_tags(evidence: Mapping[str, Any]) -> Sequence[str]:
    tags: list[str] = []
    for key in (
        "missing_deliverables",
        "admission_failure",
        "benchmark_regression",
        "benchmark_compat_regression",
        "protected_surface_violation",
        "static_contract_violation",
        "resume_mismatch",
        "reentry_mismatch",
        "artifact_mismatch",
        "schema_mismatch",
        "error_type",
    ):
        if evidence.get(key):
            tags.append(str(key))
    message = (evidence.get("message") or "").lower()
    if message:
        # Lightly classify message signal for later dashboards without storing full text
        if "import" in message:
            tags.append("msg:import")
        if "artifact" in message:
            tags.append("msg:artifact")
        if "benchmark" in message:
            tags.append("msg:benchmark")
        if "protected" in message or "static" in message:
            tags.append("msg:protected")
        if "resume" in message or "checkpoint" in message or "re-entry" in message or "reentry" in message:
            tags.append("msg:resume")
    return tuple(sorted(set(tags)))


__all__ = [
    "FailureFamily",
    "RepairTarget",
    "ClassificationRecord",
    "classify_failure_family",
    "select_repair_targets",
    "persist_classification",
    "load_recent_classifications",
    "plan_repair_from_evidence",
]
