from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional


def _load_curated_adjacent_pairs() -> List[Dict[str, Any]]:
    # Resolve curated adjacent-pair corpus from existing helpers with a defensive loader
    import agents.lib.pair_manifest as pair_manifest  # lazy import to avoid hard dependency at import time

    candidate_loaders = [
        "load_curated_adjacent_pair_corpus",
        "load_curated_adjacent_pairs",
        "load_bounded_two_task_pairs",
        "load_adjacent_pair_manifest",
        "load_curated_pair_corpus",
    ]
    for name in candidate_loaders:
        loader = getattr(pair_manifest, name, None)
        if callable(loader):
            pairs = loader()
            if isinstance(pairs, list):
                return pairs
    raise RuntimeError("No curated adjacent-pair corpus loader found in agents.lib.pair_manifest")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _safe_json_write(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=str)


def _promotion_verdict_and_checkpoint(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derive a conservative promotion/checkpoint verdict for the bounded two-task corpus.

    Keeps two non-goals explicitly blocked:
    - unattended broad multi-task autonomy
    - standalone orchestrator productization
    """
    total_pairs = int(summary.get("total_pairs", 0))
    eligible_pairs = int(summary.get("eligible_pairs", 0))
    completed = int(summary.get("completed_bounded_pilot_pairs", 0))
    blocked_adm = int(summary.get("blocked_admissions", 0))
    handoff_fail = int(summary.get("handoff_failures", 0))
    supervised = int(summary.get("supervised_interventions", 0))
    direct_completions = int(summary.get("direct_completions", 0))
    assisted_completions = int(summary.get("assisted_completions", 0))

    denom = max(eligible_pairs, 1)
    completed_rate = completed / denom
    supervised_rate = supervised / denom
    handoff_fail_rate = handoff_fail / denom
    blocked_rate = blocked_adm / max(total_pairs, 1)
    direct_rate = direct_completions / denom
    assisted_rate = assisted_completions / denom

    thresholds = {
        "min_completed_rate_to_continue": 0.3,
        "min_completed_rate_to_widen": 0.5,
        "max_supervised_rate_for_continue": 0.5,
        "max_handoff_failure_rate_for_continue": 0.4,
        "max_admission_blocked_rate_for_widen": 0.2,
    }

    # Default conservative verdict
    verdict = "conditionally_ready_under_supervision"

    if eligible_pairs == 0 or completed_rate < 0.2:
        verdict = "not_ready"
    else:
        # Consider continue vs widen conservatively
        if (
            completed_rate >= thresholds["min_completed_rate_to_widen"]
            and supervised_rate <= thresholds["max_supervised_rate_for_continue"]
            and handoff_fail_rate <= thresholds["max_handoff_failure_rate_for_continue"]
            and blocked_rate <= thresholds["max_admission_blocked_rate_for_widen"]
        ):
            verdict = "cautiously_ready_to_expand_corpus_under_supervision"
        elif (
            completed_rate >= thresholds["min_completed_rate_to_continue"]
            and supervised_rate <= thresholds["max_supervised_rate_for_continue"]
            and handoff_fail_rate <= thresholds["max_handoff_failure_rate_for_continue"]
        ):
            verdict = "ready_to_continue_bounded_pilot"
        else:
            verdict = "conditionally_ready_under_supervision"

    may_widen = verdict == "cautiously_ready_to_expand_corpus_under_supervision"

    widening_checkpoint = {
        "bounded_two_task_corpus_verdict": verdict,
        "may_widen_curated_corpus_under_supervision": bool(may_widen),
        "broad_unattended_multi_task_autonomy_blocked": True,
        "standalone_orchestrator_productization_blocked": True,
        "notes": (
            "Widening remains supervised and bounded. One-task truth surfaces are unchanged. "
            "Broader unattended multi-task autonomy and standalone productization remain blocked."
        ),
    }

    return {
        "verdict": verdict,
        "thresholds": thresholds,
        "metrics": {
            "total_pairs": total_pairs,
            "eligible_pairs": eligible_pairs,
            "completed_pairs": completed,
            "blocked_admissions": blocked_adm,
            "handoff_failures": handoff_fail,
            "supervised_interventions": supervised,
            "completed_rate": round(completed_rate, 4),
            "supervised_rate": round(supervised_rate, 4),
            "handoff_failure_rate": round(handoff_fail_rate, 4),
            "admission_blocked_rate": round(blocked_rate, 4),
            "transport_stable_direct_rate": round(direct_rate, 4),
            "supervision_assisted_rate": round(assisted_rate, 4),
            "transport_stable_direct_completions": direct_completions,
            "supervision_assisted_completions": assisted_completions,
        },
        "widening_checkpoint": widening_checkpoint,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def run_bounded_two_task_corpus_benchmark(
    session_dir: Optional[str] = None,
    pairs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Real bounded two-task corpus benchmark:
    - Loads curated adjacent pairs using existing manifest helpers if not provided.
    - Runs the real bounded pilot runner for each pair.
    - Persists durable artifacts in a two_task/bounded_corpus directory under the session_dir.
    - Writes a conservative promotion/checkpoint artifact alongside the corpus outputs.
    - Returns a summary dict with benchmark metrics.
    """
    # Resolve session/artifacts directory using existing conventions where possible.
    root_dir = session_dir or os.getcwd()
    two_task_root = os.path.join(root_dir, "two_task")
    bounded_dir = os.path.join(two_task_root, "bounded_corpus")
    _ensure_dir(bounded_dir)

    # Resolve pairs input
    resolved_pairs: List[Dict[str, Any]] = pairs if pairs is not None else _load_curated_adjacent_pairs()

    # Persist the evaluated pairs manifest for traceability
    _safe_json_write(os.path.join(bounded_dir, "pairs.json"), resolved_pairs)

    # Lazy import to allow tests to monkeypatch
    try:
        from agents.lib.bounded_pilot import run_bounded_two_task_pilot  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive in case of import shape drift
        raise RuntimeError(f"bounded pilot runner import failed: {exc}") from exc

    total_pairs = len(resolved_pairs)
    eligible_pairs = 0
    completed_bounded_pilot_pairs = 0
    blocked_admissions = 0
    handoff_failures = 0
    supervised_interventions = 0
    direct_completions = 0
    assisted_completions = 0

    for pair in resolved_pairs:
        if not bool(pair.get("eligible", False)):
            # Not eligible for bounded pilot attempt; skip metrics except total
            continue

        eligible_pairs += 1
        result = dict(run_bounded_two_task_pilot(pair, session_dir=bounded_dir) or {})

        admitted = bool(result.get("admitted"))
        completed = bool(result.get("completed"))
        handoff_failure = bool(result.get("handoff_failure"))
        supervised = bool(result.get("supervised_intervention"))

        if admitted and completed:
            completed_bounded_pilot_pairs += 1
            if supervised:
                assisted_completions += 1
            else:
                direct_completions += 1
        elif not admitted:
            blocked_admissions += 1

        if handoff_failure:
            handoff_failures += 1
        if supervised:
            supervised_interventions += 1

    summary = {
        "total_pairs": total_pairs,
        "eligible_pairs": eligible_pairs,
        "completed_bounded_pilot_pairs": completed_bounded_pilot_pairs,
        "blocked_admissions": blocked_admissions,
        "handoff_failures": handoff_failures,
        "supervised_interventions": supervised_interventions,
        "direct_completions": direct_completions,
        "assisted_completions": assisted_completions,
        "artifacts_dir": bounded_dir,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    _safe_json_write(os.path.join(bounded_dir, "summary.json"), summary)
    _safe_json_write(os.path.join(bounded_dir, "bounded_corpus_promotion.json"), _promotion_verdict_and_checkpoint(summary))

    return summary
