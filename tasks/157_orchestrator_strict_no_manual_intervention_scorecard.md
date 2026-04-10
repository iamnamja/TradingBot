Task 157 — strict no-manual-intervention scorecard

Summary
This task codifies strict autonomy accounting rules inside the benchmark/session artifact flow:
- Manual edits during a run invalidate autonomous success for that run.
- Direct and self-healed completions are recorded separately.
- Authority-blocked and supervised/escalated runs are tracked distinctly.
- A durable scorecard.json is written in the benchmark session directory alongside a legacy-compatible scoreboard.json.

Promotion policy
Promotion decisions for one-task evaluation now use the integrated session scorecard rather than ad hoc interpretation. A run invalidated by human intervention cannot be counted as an autonomous success.

Artifacts
- scorecard.json: strict integrated scorecard with category breakdowns and pass-rate fields.
- scoreboard.json: pass-rate surface maintained for backward compatibility with existing dashboards. END_FILE
