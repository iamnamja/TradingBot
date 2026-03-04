# Task 007: LLM advisor (approve/veto candidates)

## Goal
Add an LLM review layer that evaluates **deterministic candidates** produced by the strategy and can:
- approve
- veto
- request “no_trade” when uncertain

**LLM does NOT generate trades from scratch in v1.**

This task must be implemented **without** calling any external APIs. A noop implementation is required.

## Deliverables (must create these files)
- `src/tradingbot/llm/__init__.py`
- `src/tradingbot/llm/types.py`
  - `@dataclass LLMDecision` with:
    - `symbol: str`
    - `action: Literal["approve","veto","no_trade"]`
    - `reason: str`
- `src/tradingbot/llm/advisor.py`
  - `class LLMAdvisor(Protocol)`:
    - `review(candidates: list[Candidate], context: dict) -> list[LLMDecision]`
  - Use a safe import pattern for `Candidate`:
    - If `Candidate` type does not exist yet, use `TYPE_CHECKING` + `Any` at runtime so imports never break.
- `src/tradingbot/llm/noop.py`
  - `class NoopLLMAdvisor(LLMAdvisor)` that approves everything (used in tests / when disabled)

## Configuration
- Add a config flag: `llm_enabled: bool` (default `False`) in the project settings (likely `src/tradingbot/config/settings.py`).
- When `llm_enabled` is `False`, the system must use `NoopLLMAdvisor` and must never call external APIs.
- No `OPENAI_API_KEY` should be required for tests.

## Tests (must create)
- `tests/test_llm_noop.py` ensures:
  - Noop approves all candidates
  - The number of decisions equals the number of candidates
  - Each decision has `action == "approve"` and a non-empty reason (or a consistent reason string)

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- Tests do not require `OPENAI_API_KEY`
- External LLM integration (OpenAI client) can be added later behind the interface
