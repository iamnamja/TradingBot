# Task 007: LLM advisor (approve/veto candidates)

## Goal
Add an LLM layer that reviews deterministic candidates and can:
- approve
- veto
- request “no-trade” when uncertain

**LLM does NOT generate trades from scratch in v1.**

## Deliverables
- `src/tradingbot/llm/types.py`
  - `@dataclass LLMDecision` with:
    - `symbol: str`
    - `action: Literal["approve","veto","no_trade"]`
    - `reason: str`
- `src/tradingbot/llm/advisor.py`
  - `class LLMAdvisor(Protocol)`:
    - `review(candidates: list[Candidate], context: dict) -> list[LLMDecision]`
- `src/tradingbot/llm/noop.py`
  - `class NoopLLMAdvisor(LLMAdvisor)` that approves everything (used in tests / when disabled)

## Configuration
- Add a config flag: `llm_enabled: bool`
  - When `False`, system uses `NoopLLMAdvisor` and never calls external APIs.

## Tests
- `tests/test_llm_noop.py` ensures noop behavior

## Acceptance criteria
- `ruff check .` and `pytest -q` pass
- Tests do not require `OPENAI_API_KEY`
- External LLM integration (OpenAI client) can be added later behind the interface
