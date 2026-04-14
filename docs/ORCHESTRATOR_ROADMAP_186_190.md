# Orchestrator Roadmap 186–190

## Theme

Contract and model-compatibility hardening after the post-185 reliability gate.

## Why this tranche exists

The repo is now blocked less by missing pilot concepts and more by recurring contract drift:

- status narrative drift across multiple docs,
- strict GPT-style file-bundle assumptions leaking into every model path,
- and late failures when a selected model/profile cannot satisfy the task’s expected output transport.

This tranche fixes those bottlenecks before any cautious capability widening resumes.

## Task list

### 186 — docs status headline consistency guard
Introduce a durable guard so `README.md`, `docs/TRADINGBOT_PROJECT_STATE.md`, and related status docs stop drifting after successful tasks.

### 187 — model profile registry and output transport contract declaration
Make model/output behavior explicit. Define which models are expected to use strict file bundles versus patch-style transport.

### 188 — Codex patch/apply transport and dual-mode output parsing
Add a Codex-compatible path without breaking the proven GPT file-bundle path.

### 189 — provider capability negotiation and safe model fallback diagnostics
Fail early or fall back safely when a selected model/provider/profile cannot satisfy the task’s required transport contract.

### 190 — contract and model-transport checkpoint plus cautious next-slice gate
Record whether docs consistency and model-transport hardening are now stable enough to permit a cautiously bounded next capability slice.

## Non-goals for this tranche

- no broad unattended multi-task autonomy claims
- no arbitrary open-ended scheduling
- no standalone orchestrator-app unblocking
- no removal of the strict GPT file-bundle path that is already proven in this harness
