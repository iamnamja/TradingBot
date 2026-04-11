# Orchestrator Roadmap 166–170

## Theme

Third one-task reliability sprint and promotion decision.

## Why this slice exists

Tasks 157–165 materially improved the one-task lane and produced two reliability re-proofs, but the orchestrator still needs a sharper scorecard, better authority corroboration, and one more failure-family reduction pass before we can honestly say the one-task lane should become the default proving path.

This slice is still about one-task reliability first. It is not a multi-task expansion slice.

## Tasks

### 166 — strict no-manual-intervention scorecard

Tighten the benchmark/session scorecard so promotion decisions cannot over-credit runs that were only recovered because a human stepped in.

### 167 — authority corroboration and run truth

Reduce noisy authority stops by better distinguishing timing artifacts, unresolved ambiguity, and confirmed authority blocks while keeping conservative claim discipline.

### 168 — top failure family elimination tranche

Use the latest re-proof artifacts to choose the dominant real one-task failure family and land the narrowest measured fix.

### 169 — one-task promotion re-proof

Re-run the benchmark or minipack with explicit thresholds and decide whether the one-task lane is not ready, conditionally ready, or ready to become the default proving path for eligible work.

### 170 — default single-task path and two-task pilot gate

Only if the promotion result supports it, define how eligible one-task work becomes the default orchestrator path and what explicit gate must still be satisfied before any future bounded two-task pilot.

## Exit signal

Do not claim broad multi-task autonomy at the end of this slice unless the promotion verdict and the explicit pilot gate both say widening is justified.
