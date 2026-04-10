# Orchestrator Roadmap 161–165

## Theme

Single-task reliability sprint.

## Why this slice exists

Live proof-mode runs on Task 157 showed that the orchestrator can now execute real one-task work, but the main blockers are no longer architectural abstractions. They are live-run reliability problems:

- empty bundle transport failures,
- runtime artifact ambiguity,
- partial implementations that still go green,
- and incomplete integration into the benchmark/session flow.

The right next step is to make the orchestrator complete one task really well and repeatedly before returning to broader roadmap execution.

## Tasks

### 161 — benchmark scorecard integration

Integrate strict no-manual-intervention grading into the real benchmark/session artifacts and promotion path.

### 162 — empty bundle transport retry and classifier

Distinguish empty-bundle transport failures from task failures and give them one bounded transport-only retry before final failure.

### 163 — runtime artifact quarantine and subset preservation normalization

Make proof-mode artifact retention predictable so successful runs are not repeatedly blocked by the same leftover runtime files.

### 164 — completion integrity gate

Reject green-but-partial task completions when the required integration surfaces were not actually updated.

### 165 — one-task reliability minipack re-proof

Run a small fixed pack of benchmark-eligible tasks and measure whether one-task autonomous completion is becoming repeatable.

## Exit signal

Do not resume broader roadmap ambitions until the orchestrator can complete a small fixed pack of one-task benchmark work with a credible direct-completion rate and minimal manual rescue.
