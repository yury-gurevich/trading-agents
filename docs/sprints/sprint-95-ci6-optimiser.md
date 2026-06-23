# Sprint 95 — CI-6: optimiser (sweep within bounds)

**Branch:** `sprint-95-ci6-optimiser`
**Status:** queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: M**

## Goal

Close the loop: **generate** challenger ParameterSets automatically by sweeping within the CI-1
tunable bounds, run them as experiments, and surface the best for the CI-5 gate. First target: the
ingest pacing loop that DL-17 ran by hand. (Layer 4, automated.)

## Scope

**In:**
- Sweep generator: given a target process, a set of tunables, and the catalogue bounds, emit candidate
  `ParameterSet`s. **Grid first** (e.g. `chunk_size ∈ {8,10,12,15}` × `delay ∈ {45,60,90}` ×
  `sigma ∈ {4,8}`), pluggable for smarter search (random/Bayesian) later.
- Orchestrate: for each candidate, run a CI-4 experiment vs the current champion (N trials, across
  times of day for rate-limited feeds), collect RunMetrics.
- Rank by target metric subject to guardrails; present the leader to CI-5 for promotion.
- First applied target: ingest — minimise fetch time subject to **degradation rate = 0** held across
  trials (the exact DL-17 objective, now automated and recorded).

**Out:** no online/production auto-promotion without operator confirmation (gate stays operator-
triggered); smarter-than-grid search is a follow-up.

## Deliverables

- Sweep generator (grid) + orchestrator + ranking; ingest target wired.
- Tests (100% coverage) with a deterministic fake pipeline.

## Acceptance

- `optimise ingest` produces ranked candidates with RunMetrics and names a leader that holds
  degradation rate 0 at the lowest fetch time.
- The leader feeds CI-5 and, on pass, becomes the champion delivered via ACTIVATE.
- `make ci` green.

## Dependencies

- CI-1…CI-5. This is the capstone that makes "guess→run→measure→re-run" (DL-17) a system operation.
