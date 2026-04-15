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
    summary: Mapping[str, Any],
    families: Mapping[str, int],
    *,
    gpt_file_bundle_preserved: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Conservative evaluation over transport-health metrics.

    Returns a machine-readable evaluation with:
      - rates and derived fields
      - evaluated_categories flags
      - a conservative verdict:
          "not_ready" |
          "conditionally_ready_under_supervision" |
          "ready_for_cautious_bounded_next_slice"
    """
    run_count = int(summary.get("run_count", 0))
    empty_captures = int(summary.get("empty_capture_count", 0))
    bundle_fail = int(summary.get("bundle_parse_failure_count", 0))
    method_fail = int(summary.get("method_insertion_failure_count", 0))
    fallbacks = int(summary.get("fallback_count", 0))

    total_fail = bundle_fail + method_fail
    empty_rate = _rate(empty_captures, run_count)
    bundle_fail_rate = _rate(bundle_fail, run_count)
    method_fail_rate = _rate(method_fail, run_count)
    total_fail_rate = _rate(total_fail, run_count)
    fallback_rate = _rate(fallbacks, run_count)

    recurring_families_ge_2 = sum(1 for c in families.values() if int(c) >= 2)
    recurring_rate = _rate(recurring_families_ge_2, run_count)

    # Category evaluations (boolean)
    categories = {
        # Capture integrity is acceptable if empty-rate is bounded
        "capture_integrity_observed": empty_rate <= 0.10 and run_count > 0,
        # Parser-path observability: we can observe both paths when run_count>0 and any failures recorded
        "parser_path_observability_observed": run_count > 0 and (bundle_fail > 0 or method_fail > 0 or total_fail == 0),
        # Fallback tracing is acceptable if fallbacks are present but not dominating
        "protected_method_fallback_tracing_bounded": fallback_rate <= 0.5,
        # Recurring failure families should be small relative to corpus
        "recurring_failure_families_bounded": recurring_rate <= 0.10,
        # Proven GPT file-bundle path preservation (prefer explicit signal; infer conservatively if absent)
        "proven_gpt_file_bundle_path_preserved": bool(gpt_file_bundle_preserved)
        if gpt_file_bundle_preserved is not None
        else (bundle_fail_rate <= 0.33 and run_count > 0),
    }

    # Default conservative verdicts
    verdict = "not_ready"

    # Hard not-ready conditions
    if run_count == 0:
        verdict = "not_ready"
    elif empty_rate > 0.15 or total_fail_rate > 0.40:
        verdict = "not_ready"
    elif not categories["proven_gpt_file_bundle_path_preserved"]:
        verdict = "not_ready"
    else:
        # Eligible to consider "conditional" or "ready"
        # Require modest rates for conditional readiness
        if empty_rate <= 0.10 and total_fail_rate <= 0.30:
            verdict = "conditionally_ready_under_supervision"

            # Extremely conservative "ready" gate:
            # - Sufficient sample size
            # - Very low empty-capture and failure rates
            # - Fallbacks bounded clearly
            # - Recurring families are negligible
            if (
                run_count >= 20
                and empty_rate <= 0.05
                and total_fail_rate <= 0.20
                and fallback_rate <= 0.30
                and categories["recurring_failure_families_bounded"]
            ):
                verdict = "ready_for_cautious_bounded_next_slice"

    evaluation: Dict[str, Any] = {
        "rates": {
            "empty_rate": round(empty_rate, 4),
            "bundle_fail_rate": round(bundle_fail_rate, 4),
            "method_fail_rate": round(method_fail_rate, 4),
            "total_fail_rate": round(total_fail_rate, 4),
            "fallback_rate": round(fallback_rate, 4),
            "recurring_family_rate": round(recurring_rate, 4),
        },
        "counts": {
            "run_count": run_count,
            "empty_captures": empty_captures,
            "bundle_fail": bundle_fail,
            "method_fail": method_fail,
            "fallbacks": fallbacks,
            "recurring_families_ge_2": recurring_families_ge_2,
        },
        "evaluated_categories": categories,
        "verdict": verdict,
        "policy": {
            "broad_unattended_multi_task_autonomy": "blocked",
            "standalone_productization": "blocked",
            "cautious_next_slice_allowed": verdict
            in {"conditionally_ready_under_supervision", "ready_for_cautious_bounded_next_slice"},
        },
    }
    return evaluation


def write_transport_stability_checkpoint(
    base_dir: Path,
    evaluation: Mapping[str, Any],
    *,
    evidence_snapshot: Optional[Mapping[str, Any]] = None,
) -> Path:
    """
    Persist a conservative transport-stability checkpoint artifact.

    - _transport_stability_checkpoint.json
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / "_transport_stability_checkpoint.json"
    payload = {
        "checkpoint_kind": "transport_stability_checkpoint",
        "evaluation": dict(evaluation),
        "evidence": dict(evidence_snapshot) if evidence_snapshot is not None else {},
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path


def compute_and_write_transport_stability(
    corpus: Iterable[Mapping[str, Any]],
    base_dir: Path,
    *,
    gpt_file_bundle_preserved: Optional[bool] = None,
    evidence_snapshot: Optional[Mapping[str, Any]] = None,
) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, Any], Path]:
    """
    Aggregate, evaluate conservatively, and persist a transport-stability checkpoint.
    """
    summary, families = aggregate_transport_health(corpus)
    evaluation = evaluate_transport_stability_gate(
        summary, families, gpt_file_bundle_preserved=gpt_file_bundle_preserved
    )
    checkpoint_path = write_transport_stability_checkpoint(
        base_dir, evaluation, evidence_snapshot=evidence_snapshot
    )
    return summary, families, evaluation, checkpoint_path
