from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Tuple


__all__ = [
    "TransportHealthSummary",
    "aggregate_transport_health",
    "write_transport_health",
    "compute_and_write_transport_health",
]


@dataclass(frozen=True)
class TransportHealthSummary:
    run_count: int
    empty_capture_count: int
    bundle_parse_failure_count: int
    method_insertion_failure_count: int
    fallback_count: int

    def to_dict(self) -> Dict[str, int]:
        return {
            "run_count": self.run_count,
            "empty_capture_count": self.empty_capture_count,
            "bundle_parse_failure_count": self.bundle_parse_failure_count,
            "method_insertion_failure_count": self.method_insertion_failure_count,
            "fallback_count": self.fallback_count,
        }


def _is_empty_capture(status: Any) -> bool:
    # Task 191 status values; consider anything not exactly "non_empty" as empty/problematic
    return status is not None and status != "non_empty"


def _is_bundle_path(parser_path: Any) -> bool:
    return parser_path == "bundle"


def _is_method_insertion_path(parser_path: Any) -> bool:
    return parser_path in ("protected_method", "method_insertion", "protected")


def aggregate_transport_health(
    corpus: Iterable[Mapping[str, Any]]
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Aggregate transport-health metrics from a synthetic or live corpus.

    Each record may contain:
      - raw_capture_status: str (Task 191 classification)
      - parser_path: "bundle" | "protected_method" | "method_insertion"
      - success: bool
      - failure_family: str
      - fallback_applied: bool

    Returns:
      - summary dict
      - recurring failure-family histogram dict
    """
    run_count = 0
    empty_capture_count = 0
    bundle_parse_failure_count = 0
    method_insertion_failure_count = 0
    fallback_count = 0
    families: Dict[str, int] = {}

    for rec in corpus:
        run_count += 1

        status = rec.get("raw_capture_status")
        if _is_empty_capture(status):
            empty_capture_count += 1

        parser_path = rec.get("parser_path")
        success = bool(rec.get("success", False))
        if not success:
            if _is_bundle_path(parser_path):
                bundle_parse_failure_count += 1
            elif _is_method_insertion_path(parser_path):
                method_insertion_failure_count += 1

            fam = rec.get("failure_family") or rec.get("failure_category")
            if isinstance(fam, str) and fam:
                families[fam] = families.get(fam, 0) + 1

        if rec.get("fallback_applied") is True:
            fallback_count += 1

    summary = TransportHealthSummary(
        run_count=run_count,
        empty_capture_count=empty_capture_count,
        bundle_parse_failure_count=bundle_parse_failure_count,
        method_insertion_failure_count=method_insertion_failure_count,
        fallback_count=fallback_count,
    ).to_dict()

    return summary, families


def write_transport_health(
    base_dir: Path,
    summary: Mapping[str, Any],
    families: Mapping[str, int],
) -> Tuple[Path, Path]:
    """
    Persist transport-health artifacts:

      - _transport_health_summary.json
      - _transport_failure_families.json
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    summary_path = base_dir / "_transport_health_summary.json"
    families_path = base_dir / "_transport_failure_families.json"

    summary_path.write_text(json.dumps(dict(summary), indent=2, sort_keys=True))
    families_path.write_text(json.dumps(dict(families), indent=2, sort_keys=True))

    return summary_path, families_path


def compute_and_write_transport_health(
    corpus: Iterable[Mapping[str, Any]],
    base_dir: Path,
) -> Tuple[Dict[str, int], Dict[str, int], Path, Path]:
    """
    Convenience wrapper: aggregate from corpus, then write artifacts.
    """
    summary, families = aggregate_transport_health(corpus)
    s_path, f_path = write_transport_health(base_dir, summary, families)
    return summary, families, s_path, f_path
