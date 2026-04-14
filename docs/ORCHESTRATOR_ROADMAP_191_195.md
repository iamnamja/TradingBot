# Orchestrator Roadmap 191–195

## Purpose

After Task 190, the next proven bottleneck is transport stability and observability.

The project now knows:
- model profiles and transport contracts are explicit,
- fallback discipline exists,
- but some automated runs still fail before lint/tests with effectively empty raw output and empty parsed bundles.

So this tranche focuses on making those failures observable, classifiable, and less frequent.

## Tasks

### 191 — raw model output capture integrity and non-empty artifact guarantee
Guarantee that transport failures either preserve non-empty raw output artifacts or emit an explicit capture-failure reason.

### 192 — transport failure artifact expansion and parser-path observability
Persist richer transport-failure artifacts with parser path, required transport, selected transport, retry count, and artifact lengths.

### 193 — protected-method preflight, fallback tracing, and retry discipline
Make protected-method mode explicitly record why it was selected, whether fallback was attempted, and how retries were shaped.

### 194 — transport health benchmark and recurring failure-family corpus
Benchmark transport health over real runs and classify recurring transport-family failures.

### 195 — transport stability checkpoint and cautious autonomy-resume gate
Record whether transport behavior is now stable enough to justify a cautious next slice, while keeping broad autonomy blocked unless evidence improves.
