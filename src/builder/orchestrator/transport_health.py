from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


__all__ = [
    "TransportHealthSummary",
    "aggregate_transport_health",
    "write_transport_health",
    "compute_and_write_transport_health",
    "evaluate_transport_stability_gate",
    "write_transport_stability_checkpoint",
    "compute_and_write_transport_stability",
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


def _rate(n: int, d: int) -> float:
    return (n / d) if d else 0.0


def evaluate_transport_stability_gate(
    summary: Mapping[str, int],
    families: Mapping[str, int],
    *,
    gpt_file_bundle_preserved: bool,
    min_sample_size: int = 10,
    max_empty_rate: float = 0.15,
    max_parse_failure_rate: float = 0.20,
    max_fallback_rate: float = 0.50,
) -> Dict[str, Any]:
    """
    Conservative evaluation of transport stability after Tasks 191-195.

    Returns a dictionary with:
      - verdict: str (not_ready | conditionally_ready_under_supervision)
      - counts: dict
      - thresholds: dict
      - rates: dict
      - evaluated_categories: dict
      - recurring_failure_families: dict
    """
    run_count = int(summary.get("run_count", 0))
    empty_capture_count = int(summary.get("empty_capture_count", 0))
    bundle_fail = int(summary.get("bundle_parse_failure_count", 0))
    method_fail = int(summary.get("method_insertion_failure_count", 0))
    fallback_count = int(summary.get("fallback_count", 0))

    empty_rate = _rate(empty_capture_count, run_count)
    parse_fail_rate = _rate(bundle_fail + method_fail, run_count)
    fallback_rate = _rate(fallback_count, run_count)

    evaluated_categories = {
        "proven_gpt_file_bundle_path_preserved": bool(gpt_file_bundle_preserved),
        "empty_capture_rate_within_bounds": empty_rate <= max_empty_rate,
        "parse_failure_rates_within_bounds": parse_fail_rate <= max_parse_failure_rate,
        "fallback_rate_within_bounds": fallback_rate <= max_fallback_rate,
        "sample_size_sufficient": run_count >= min_sample_size,
    }

    # Default to conservative posture
    verdict = "not_ready"
    if evaluated_categories["proven_gpt_file_bundle_path_preserved"]:
        healthy = (
            evaluated_categories["empty_capture_rate_within_bounds"]
            and evaluated_categories["parse_failure_rates_within_bounds"]
            and evaluated_categories["fallback_rate_within_bounds"]
        )
        # Even if healthy, require sufficient sample size for "ready"; keep conservative -> conditional at best.
        if healthy:
            verdict = "conditionally_ready_under_supervision"
        else:
            verdict = "not_ready"

    return {
        "verdict": verdict,
        "counts": {
            "run_count": run_count,
            "empty_capture_count": empty_capture_count,
            "bundle_parse_failure_count": bundle_fail,
            "method_insertion_failure_count": method_fail,
            "fallback_count": fallback_count,
        },
        "thresholds": {
            "min_sample_size": min_sample_size,
            "max_empty_rate": max_empty_rate,
            "max_parse_failure_rate": max_parse_failure_rate,
            "max_fallback_rate": max_fallback_rate,
        },
        "rates": {
            "empty_rate": round(empty_rate, 4),
            "parse_failure_rate": round(parse_fail_rate, 4),
            "fallback_rate": round(fallback_rate, 4),
        },
        "evaluated_categories": evaluated_categories,
        "recurring_failure_families": dict(sorted(families.items())),
        "policy": {
            "widening_scope": "bounded_supervised_only",
            "unattended_multi_task_autonomy": "blocked",
            "standalone_productization": "blocked",
        },
        "notes": "Evaluation remains conservative; small/healthy samples are treated as conditional readiness at best.",
    }


def write_transport_stability_checkpoint(
    base_dir: Path,
    evaluation: Mapping[str, Any],
    *,
    evidence_snapshot: Optional[Mapping[str, Any]] = None,
) -> Path:
    """
    Persist a conservative transport-stability checkpoint artifact.
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / "_transport_stability_checkpoint.json"
    payload: Dict[str, Any] = {
        "checkpoint_kind": "transport_stability_checkpoint",
        "evaluation": dict(evaluation),
    }
    if evidence_snapshot is not None:
        payload["evidence"] = dict(evidence_snapshot)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path


def compute_and_write_transport_stability(
    corpus: Iterable[Mapping[str, Any]],
    base_dir: Path,
    *,
    gpt_file_bundle_preserved: bool = True,
) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, Any], Path, Path, Path]:
    """
    Aggregate health, evaluate stability, and persist all artifacts.

    Returns:
      summary, families, evaluation, summary_path, families_path, checkpoint_path
    """
    summary, families, s_path, f_path = compute_and_write_transport_health(corpus, base_dir)
    evaluation = evaluate_transport_stability_gate(summary, families, gpt_file_bundle_preserved=gpt_file_bundle_preserved)
    checkpoint_path = write_transport_stability_checkpoint(base_dir, evaluation, evidence_snapshot={"summary": summary, "families": families})
    return summary, families, evaluation, s_path, f_path, checkpoint_path
