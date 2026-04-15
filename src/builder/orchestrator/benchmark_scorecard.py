from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Union


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Scorecard:
    total_runs: int = 0
    direct_completions: int = 0
    self_healed_completions: int = 0
    failed_runs: int = 0
    authority_blocked_runs: int = 0
    supervised_runs: int = 0
    invalidated_by_human_intervention: int = 0

    def successes(self) -> int:
        return self.direct_completions + self.self_healed_completions

    def failures(self) -> int:
        # Failures are everything that is not counted as an autonomous success.
        return max(self.total_runs - self.successes(), 0)

    def pass_rate(self) -> float:
        return self.successes() / self.total_runs if self.total_runs else 0.0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["successes"] = self.successes()
        data["failures"] = self.failures()
        data["pass_rate"] = round(self.successes() / self.total_runs, 4) if self.total_runs else 0.0
        return data

    def _rates(self) -> Dict[str, float]:
        total = self.total_runs or 1  # avoid div-by-zero
        return {
            "pass_rate": self.pass_rate(),
            "direct_rate": self.direct_completions / total,
            "self_healed_rate": self.self_healed_completions / total,
            "supervised_rate": self.supervised_runs / total,
            "authority_ambiguity_rate": self.authority_blocked_runs / total,
            "invalidated_rate": self.invalidated_by_human_intervention / total,
        }


@dataclass(frozen=True)
class PromotionThresholds:
    # Minimum autonomous completion rate across the curated one-task set
    min_pass_rate: float = 0.6
    # "Materially better" margin for direct vs self-healed completions
    min_direct_minus_self_healed_margin: float = 0.2
    # Supervision/escalation rate must remain low
    max_supervised_rate: float = 0.1
    # Unresolved authority-ambiguity must remain very low
    max_authority_ambiguity_rate: float = 0.05
    # No recurring compatibility seam regressions allowed in the benchmark set
    require_no_compat_regressions: bool = True


@dataclass(frozen=True)
class EmptyOutputGuard:
    """Small regression guard configuration for empty-output failures."""
    max_empty_output_rate: float = 0.10


class BenchmarkSession:
    """
    Integrated scorecard writer for benchmark sessions.

    This session integrates a strict no-manual-intervention scorecard directly into the
    benchmark session artifact directory. It preserves the existing pass-rate scoreboard
    surface while adding a durable scorecard.json with full, strict counts.

    It also produces a promotion.json artifact with an explicit verdict and thresholds.
    """

    def __init__(self, session_dir: Path):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.scorecard = Scorecard()

    def record_run(
        self,
        *,
        direct_completion: bool = False,
        self_healed_completion: bool = False,
        failed: bool = False,
        authority_blocked: bool = False,
        supervised: bool = False,
        manual_edit: bool = False,
    ) -> None:
        """
        Record a single benchmark run result into the session.

        Strict no-manual-intervention rule:
        - If manual_edit is True, the run is not counted as an autonomous success,
          even if it otherwise looks like a direct or self-healed completion.
        - The run is tracked under 'invalidated_by_human_intervention' and treated as
          a failure for the pass-rate scoreboard surface.
        """
        self.scorecard.total_runs += 1

        if manual_edit:
            self.scorecard.invalidated_by_human_intervention += 1
            # If caller didn't specify another explicit non-success bucket, count it as failure.
            if not (failed or authority_blocked or supervised):
                self.scorecard.failed_runs += 1
            return

        if authority_blocked:
            self.scorecard.authority_blocked_runs += 1
            return

        if supervised:
            self.scorecard.supervised_runs += 1
            return

        if direct_completion:
            self.scorecard.direct_completions += 1
            return

        if self_healed_completion:
            self.scorecard.self_healed_completions += 1
            return

        # Default fallthrough: failed run (unknown or explicit failure)
        if failed:
            self.scorecard.failed_runs += 1
        else:
            # Treat unknown outcome as failure for conservative pass-rate compatibility
            self.scorecard.failed_runs += 1

    def write_artifacts(self) -> None:
        """
        Persist both the integrated strict scorecard and the legacy-compatible scoreboard.

        - scorecard.json: durable strict scorecard with full counts.
        - scoreboard.json: preserved pass-rate surface used by prior tasks.
        """
        scorecard_path = self.session_dir / "scorecard.json"
        with scorecard_path.open("w", encoding="utf-8") as f:
            json.dump(self.scorecard.to_dict(), f, indent=2, sort_keys=True)

        scoreboard = {
            "total": self.scorecard.total_runs,
            "successes": self.scorecard.successes(),
            "failures": self.scorecard.failures(),
            "pass_rate": round(self.scorecard.pass_rate(), 4),
            # Compatibility extensions for richer dashboards:
            "direct_completions": self.scorecard.direct_completions,
            "self_healed_completions": self.scorecard.self_healed_completions,
        }
        with (self.session_dir / "scoreboard.json").open("w", encoding="utf-8") as f:
            json.dump(scoreboard, f, indent=2, sort_keys=True)

    @staticmethod
    def default_thresholds() -> PromotionThresholds:
        return PromotionThresholds()

    def _promotion_verdict(
        self,
        thresholds: PromotionThresholds,
        *,
        compatibility_regressions_detected: bool = False,
    ) -> dict:
        rates = self.scorecard._rates()
        pass_rate = rates["pass_rate"]
        direct_rate = rates["direct_rate"]
        self_healed_rate = rates["self_healed_rate"]
        supervised_rate = rates["supervised_rate"]
        authority_rate = rates["authority_ambiguity_rate"]

        if self.scorecard.total_runs == 0:
            verdict = "not_ready"
        elif thresholds.require_no_compat_regressions and compatibility_regressions_detected:
            verdict = "not_ready"
        elif pass_rate >= thresholds.min_pass_rate and \
            (direct_rate - self_healed_rate) >= thresholds.min_direct_minus_self_healed_margin and \
            supervised_rate <= thresholds.max_supervised_rate and \
            authority_rate <= thresholds.max_authority_ambiguity_rate:
            verdict = "ready_to_be_default"
        elif pass_rate >= thresholds.min_pass_rate and direct_rate >= self_healed_rate:
            verdict = "conditionally_ready_under_supervision"
        else:
            verdict = "not_ready"

        payload = {
            "created_at": _utc_now_iso(),
            "thresholds": asdict(thresholds),
            "metrics": {
                "total_runs": self.scorecard.total_runs,
                "successes": self.scorecard.successes(),
                "failures": self.scorecard.failures(),
                **rates,
            },
            "compatibility_regressions_detected": bool(compatibility_regressions_detected),
            "verdict": verdict,
        }
        return payload

    def persist_promotion_verdict(
        self,
        thresholds: PromotionThresholds | None = None,
        *,
        compatibility_regressions_detected: bool = False,
    ) -> dict:
        """
        Compute and persist the promotion verdict alongside score artifacts.

        Returns the written payload.
        """
        t = thresholds or self.default_thresholds()
        payload = self._promotion_verdict(t, compatibility_regressions_detected=compatibility_regressions_detected)
        path = self.session_dir / "promotion.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        return payload

    def close(self) -> None:
        self.write_artifacts()
        # Persist a promotion verdict using default thresholds. The orchestrator benchmark
        # harness may overwrite with a more specialized decision if needed.
        self.persist_promotion_verdict()

    # Optional helper for callers who want to persist a guard artifact alongside promotions.
    def apply_empty_output_regression_guard(
        self,
        *,
        empty_output_rate: float,
        guard: EmptyOutputGuard | None = None,
    ) -> dict:
        """
        Evaluate a small empty-output regression guard and persist a guard artifact.

        Note: This helper does not change the baseline promotion verdict. Callers
        may choose to degrade promotion.json separately for conservative behavior.
        """
        g = guard or EmptyOutputGuard()
        promo_path = self.session_dir / "promotion.json"
        baseline_verdict = "not_ready"
        if promo_path.exists():
            try:
                baseline_verdict = json.loads(promo_path.read_text(encoding="utf-8")).get("verdict", "not_ready")
            except Exception:
                baseline_verdict = "not_ready"

        triggered = empty_output_rate > g.max_empty_output_rate
        payload = {
            "created_at": _utc_now_iso(),
            "empty_output": {
                "empty_output_rate": round(empty_output_rate, 6),
                "max_allowed_rate": g.max_empty_output_rate,
                "guard_triggered": bool(triggered),
            },
            "verdict_baseline": baseline_verdict,
            "verdict_with_guard": "not_ready" if triggered else baseline_verdict,
        }
        guard_path = self.session_dir / "promotion_guard.json"
        with guard_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        return payload


def open_session(session_dir: Union[str, Path]) -> BenchmarkSession:
    """
    Open a benchmark session bound to the given artifact directory.

    The returned session writes its integrated scorecard into the provided path.
    """
    return BenchmarkSession(Path(session_dir))
