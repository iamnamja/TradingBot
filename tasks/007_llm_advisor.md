# Task 007: LLM advisor (approve/veto candidates)

## Goal
Add an LLM layer that reviews deterministic candidates and can:
- approve
- veto
- request “no-trade” for uncertainty

LLM does NOT generate trades from scratch in v1.

## Scope
- Define `LLMAdvisor` interface:
  - `review(candidates, context) -> decisions`
- Context may include:
  - latest indicators snapshot
  - market regime summary (optional)
- Add prompt template stored in repo (non-secret)

## Safety/Controls
- LLM can only:
  - veto OR approve within same action type
- Hard rule: execution requires passing risk gate regardless of LLM approval

## Acceptance Criteria
- If LLM disabled via config, system bypasses with “approved by default”
- If enabled, decisions are logged with rationale (not chain-of-thought; just summary)

## Tests
- Unit test with mocked LLM responses
- Ensure veto prevents execution

## Notes for Agents
- Keep provider flexible (OpenAI/Claude)
- Do not commit API keys