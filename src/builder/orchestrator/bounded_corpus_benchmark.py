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

    denom = max(eligible_pairs, 1)
    completed_rate = completed / denom
    supervised_rate = supervised / denom
    handoff_fail_rate = handoff_fail / denom
    blocked_rate = blocked_adm / max(total_pairs, 1)

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

    # Load corpus manifest of adjacent pairs if not explicitly provided
    if pairs is None:
        pairs = _load_curated_adjacent_pairs()

    # Real bounded pilot runner (supervised runner)
    from agents.lib.bounded_pilot import run_bounded_two_task_pilot  # lazy import to keep default paths safe

    total_pairs = len(pairs)
    eligible_count = 0
    ineligible_count = 0
    completed_count = 0
    blocked_admissions_count = 0
    handoff_failures_count = 0
    supervised_interventions_count = 0

    per_pair_results: List[Dict[str, Any]] = []

    for idx, pair in enumerate(pairs):
        pair_id = pair.get("id") or f"pair_{idx+1}"
        pair_dir = os.path.join(bounded_dir, str(pair_id))
        _ensure_dir(pair_dir)

        result: Dict[str, Any]
        error: Optional[str] = None

        try:
            # Invoke the real bounded two-task runner.
            # We pass a session-scoped pair directory to allow the runner to persist its own ledger/artifacts.
            result = run_bounded_two_task_pilot(pair, session_dir=pair_dir)
        except Exception as exc:  # noqa: BLE001 - capture and continue
            # Treat exceptions as handoff/runner failures for benchmark accounting purposes.
            error = f"{type(exc).__name__}: {exc}"
            result = {
                "status": "error",
                "error": error,
                "admitted": None,
                "completed": False,
                "handoff_failure": True,
                "supervised_intervention": False,
            }

        # Normalize flags using supervised-intervention and pilot-failure digest truth where available.
        admitted = result.get("admitted")
        admission_blocked = bool(
            (admitted is False)
            or result.get("admission_blocked")
            or result.get("blocked_admission")
            or (result.get("status") == "blocked")
        )
        completed = bool(
            result.get("completed")
            or (result.get("status") == "completed")
            or (result.get("result") == "completed")
        )
        handoff_failure = bool(
            result.get("handoff_failure")
            or (result.get("handoff", {}).get("failed") if isinstance(result.get("handoff"), dict) else False)
            or (result.get("failure") == "handoff")
            or (result.get("status") == "handoff_failed")
            or (error is not None)
        )
        supervised_intervention = bool(
            result.get("supervised_intervention")
            or (result.get("supervision", {}).get("intervened") if isinstance(result.get("supervision"), dict) else False)
            or (result.get("intervention") == "supervised")
        )

        # Eligibility accounting: prefer manifest truth if present; otherwise derive from admission.
        manifest_eligible = pair.get("eligible")
        if manifest_eligible is None:
            eligible = not admission_blocked
        else:
            eligible = bool(manifest_eligible)

        # Update counters
        if eligible:
            eligible_count += 1
        else:
            ineligible_count += 1
        if admission_blocked:
            blocked_admissions_count += 1
        if completed:
            completed_count += 1
        if handoff_failure:
            handoff_failures_count += 1
        if supervised_intervention:
            supervised_interventions_count += 1

        # Persist per-pair raw result envelope for durable supervision/failure truth
        per_pair_summary = {
            "pair_id": pair_id,
            "eligible": eligible,
            "admission_blocked": admission_blocked,
            "completed": completed,
            "handoff_failure": handoff_failure,
            "supervised_intervention": supervised_intervention,
            "error": error,
        }
        per_pair_results.append(per_pair_summary)

        # Write pair-level artifact with raw runner result to facilitate durable truth re-use
        _safe_json_write(os.path.join(pair_dir, "result.json"), result)

    # Persist bounded corpus artifacts separated from one-task truth surfaces
    manifest_out = {
        "pairs": per_pair_results,
        "total_pairs": total_pairs,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _safe_json_write(os.path.join(bounded_dir, "pairs.json"), manifest_out)

    summary = {
        "total_pairs": total_pairs,
        "eligible_pairs": eligible_count,
        "ineligible_pairs": ineligible_count,
        "completed_bounded_pilot_pairs": completed_count,
        "blocked_admissions": blocked_admissions_count,
        "handoff_failures": handoff_failures_count,
        "supervised_interventions": supervised_interventions_count,
        "artifacts_dir": bounded_dir,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _safe_json_write(os.path.join(bounded_dir, "summary.json"), summary)

    # Write a promotion/checkpoint artifact for the bounded corpus evidence
    promotion = _promotion_verdict_and_checkpoint(summary)
    _safe_json_write(os.path.join(bounded_dir, "bounded_corpus_promotion.json"), promotion)

    return summary
