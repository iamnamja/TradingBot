import json
import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class ReliabilityMetrics:
    lane: str
    run_count: int = 0
    green_count: int = 0
    retry_total: int = 0
    failure_family_counts: Dict[str, int] = field(default_factory=dict)
    supervision_events: int = 0
    supervision_rate: float = 0.0
    admission_block_count: int = 0
    compatibility_regression_count: int = 0
    source_artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "lane": self.lane,
            "run_count": self.run_count,
            "green_count": self.green_count,
            "retry_total": self.retry_total,
            "failure_family_counts": dict(self.failure_family_counts),
            "supervision_events": self.supervision_events,
            "supervision_rate": round(self.supervision_rate, 4),
            "admission_block_count": self.admission_block_count,
            "compatibility_regression_count": self.compatibility_regression_count,
            "source_artifacts": list(self.source_artifacts),
        }


def _normalize_failure_families(entry: Dict[str, object]) -> Iterable[str]:
    # Accept either a single "failure_family" string or a list under "failure_families".
    if "failure_families" in entry and isinstance(entry["failure_families"], list):
        for fam in entry["failure_families"]:
            if isinstance(fam, str) and fam:
                yield fam
    elif "failure_family" in entry and isinstance(entry["failure_family"], str):
        if entry["failure_family"]:
            yield entry["failure_family"]


def compute_lane_reliability(runs: List[Dict[str, object]], lane: str) -> ReliabilityMetrics:
    metrics = ReliabilityMetrics(lane=lane)
    metrics.run_count = len(runs)
    failure_counts: Dict[str, int] = {}

    for r in runs:
        status = str(r.get("status", "")).lower()
        if status == "green":
            metrics.green_count += 1

        retries = r.get("retries", 0)
        if isinstance(retries, int):
            metrics.retry_total += retries

        supervised = bool(r.get("supervised", False))
        if supervised:
            metrics.supervision_events += 1

        admission_blocked = bool(r.get("admission_blocked", False))
        if admission_blocked:
            metrics.admission_block_count += 1

        compat_regression = bool(r.get("compatibility_regression", False))
        if compat_regression:
            metrics.compatibility_regression_count += 1

        for fam in _normalize_failure_families(r):
            failure_counts[fam] = failure_counts.get(fam, 0) + 1

    metrics.failure_family_counts = failure_counts
    if metrics.run_count > 0:
        metrics.supervision_rate = metrics.supervision_events / metrics.run_count
    else:
        metrics.supervision_rate = 0.0

    return metrics


def build_reliability_matrix(
    one_task_runs: Optional[List[Dict[str, object]]] = None,
    two_task_sessions: Optional[List[Dict[str, object]]] = None,
) -> Dict[str, Dict[str, object]]:
    one_task_runs = one_task_runs or []
    two_task_sessions = two_task_sessions or []

    one_metrics = compute_lane_reliability(one_task_runs, lane="one_task")
    two_metrics = compute_lane_reliability(two_task_sessions, lane="two_task")

    return {
        "one_task": one_metrics.to_dict(),
        "two_task": two_metrics.to_dict(),
    }


def _safe_read_json(path: str) -> Optional[object]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _attempt_extract_runs_from_known_one_task_artifacts(base_dir: str) -> Tuple[List[Dict[str, object]], List[str]]:
    # Conservative, optional extraction from known one-task artifacts if present.
    # This function is best-effort, never required for operation.
    sources: List[str] = []
    runs: List[Dict[str, object]] = []

    # Common strict one-task artifacts.
    scorecard = os.path.join(base_dir, "scorecard.json")
    scoreboard = os.path.join(base_dir, "scoreboard.json")
    promotion = os.path.join(base_dir, "promotion.json")

    # Only read; never modify. Keep additive posture.
    for p in (scorecard, scoreboard, promotion):
        if os.path.exists(p):
            data = _safe_read_json(p)
            if data is None:
                continue
            sources.append(os.path.relpath(p, start=base_dir))
            # Very conservative probes for possible shapes; ignore if not present.
            if isinstance(data, dict):
                if isinstance(data.get("runs"), list):
                    for item in data["runs"]:
                        if isinstance(item, dict):
                            runs.append(item)
                elif isinstance(data.get("sessions"), list):
                    for item in data["sessions"]:
                        if isinstance(item, dict):
                            runs.append(item)

    return runs, sources


def _attempt_extract_runs_from_known_two_task_artifacts(base_dir: str) -> Tuple[List[Dict[str, object]], List[str]]:
    # Conservative, optional extraction from canary and bounded-corpus artifacts.
    sources: List[str] = []
    sessions: List[Dict[str, object]] = []

    canary_trials = os.path.join(base_dir, "canary_trials.json")
    canary_scorecard = os.path.join(base_dir, "canary_scorecard.json")
    # Bounded corpus artifacts live under two_task/bounded_corpus/.
    bounded_corpus_dir = os.path.join(base_dir, "two_task", "bounded_corpus")
    bounded_pairs = os.path.join(bounded_corpus_dir, "pairs.json")
    bounded_summary = os.path.join(bounded_corpus_dir, "summary.json")
    bounded_promotion = os.path.join(bounded_corpus_dir, "bounded_corpus_promotion.json")

    for p in (canary_trials, canary_scorecard, bounded_pairs, bounded_summary, bounded_promotion):
        if os.path.exists(p):
            data = _safe_read_json(p)
            if data is None:
                continue
            sources.append(os.path.relpath(p, start=base_dir))
            if isinstance(data, dict):
                if isinstance(data.get("runs"), list):
                    for item in data["runs"]:
                        if isinstance(item, dict):
                            sessions.append(item)
                if isinstance(data.get("sessions"), list):
                    for item in data["sessions"]:
                        if isinstance(item, dict):
                            sessions.append(item)
                if isinstance(data.get("pairs"), list):
                    for item in data["pairs"]:
                        if isinstance(item, dict):
                            sessions.append(item)

    return sessions, sources


def write_reliability_artifacts(base_dir: str, matrix: Dict[str, Dict[str, object]]) -> Dict[str, str]:
    reliability_dir = os.path.join(base_dir, "reliability")
    os.makedirs(reliability_dir, exist_ok=True)

    one_path = os.path.join(reliability_dir, "one_task_reliability.json")
    two_path = os.path.join(reliability_dir, "two_task_reliability.json")
    matrix_path = os.path.join(reliability_dir, "reliability_matrix.json")

    # Persist separate lane files plus combined matrix.
    with open(one_path, "w", encoding="utf-8") as f:
        json.dump(matrix.get("one_task", {}), f, indent=2, sort_keys=True)

    with open(two_path, "w", encoding="utf-8") as f:
        json.dump(matrix.get("two_task", {}), f, indent=2, sort_keys=True)

    with open(matrix_path, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2, sort_keys=True)

    return {
        "one_task": one_path,
        "two_task": two_path,
        "matrix": matrix_path,
    }


def run_reliability_benchmark(
    base_dir: str,
    one_task_runs: Optional[List[Dict[str, object]]] = None,
    two_task_sessions: Optional[List[Dict[str, object]]] = None,
) -> Dict[str, str]:
    # If synthetic inputs are not provided, attempt conservative, read-only extraction
    # from known additive artifacts. Never write to or modify those sources.
    extracted_sources: Dict[str, List[str]] = {"one_task": [], "two_task": []}

    if one_task_runs is None:
        runs, sources = _attempt_extract_runs_from_known_one_task_artifacts(base_dir)
        one_task_runs = runs
        extracted_sources["one_task"] = sources

    if two_task_sessions is None:
        sessions, sources = _attempt_extract_runs_from_known_two_task_artifacts(base_dir)
        two_task_sessions = sessions
        extracted_sources["two_task"] = sources

    matrix = build_reliability_matrix(one_task_runs=one_task_runs, two_task_sessions=two_task_sessions)

    # Annotate source artifacts for traceability where available.
    if extracted_sources["one_task"]:
        matrix["one_task"]["source_artifacts"] = extracted_sources["one_task"]
    if extracted_sources["two_task"]:
        matrix["two_task"]["source_artifacts"] = extracted_sources["two_task"]

    return write_reliability_artifacts(base_dir, matrix)


__all__ = [
    "ReliabilityMetrics",
    "compute_lane_reliability",
    "build_reliability_matrix",
    "write_reliability_artifacts",
    "run_reliability_benchmark",
]
