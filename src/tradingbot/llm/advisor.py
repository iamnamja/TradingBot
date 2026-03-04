from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

from .types import LLMDecision

# We want a stable interface, but the Candidate type may live elsewhere (or not exist yet).
# Keep runtime imports safe so tests and imports never break.
if TYPE_CHECKING:
    try:
        # Adjust this import later when Candidate is introduced.
        from tradingbot.types import Candidate  # type: ignore
    except Exception:  # pragma: no cover
        Candidate = Any  # type: ignore
else:
    Candidate = Any  # type: ignore


class LLMAdvisor(Protocol):
    """Interface for an LLM advisor that reviews deterministic candidates."""

    def review(self, candidates: list[Candidate], context: dict[str, Any]) -> list[LLMDecision]:
        """Review candidates and return per-candidate decisions."""
        ...
