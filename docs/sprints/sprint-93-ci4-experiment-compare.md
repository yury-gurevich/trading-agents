# Sprint 93 — CI-4: experiment + compare

**Branch:** `sprint-93-ci4-experiment-compare`
**Status:** queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: M**

## Goal

Run a **champion vs challenger** ParameterSet against the **same `as_of`** and tabulate the metric
deltas, so a parameter change is judged on evidence, not a single eyeballed trace. (Layer 3→4 bridge.)

## Scope

**In:**
- `Experiment` graph node: `{id, as_of, champion_set_id, challenger_set_id, created_at}`; edges to the
  two `RunMetrics` sets it compares.
- A runner that executes the pipeline twice (or N times for variance) for the two sets on one as_of,
  writing RunMetrics for each, then a comparison: per-metric delta + win/lose/tie vs declared
  direction (e.g. degradation rate ↓ better, IC ↑ better).
- Surface: `experiment <id>` prints the side-by-side table (reuse the compare_aura.py table style).
- Multi-run support to average out time-of-day variance (DL-17 run 3 showed Finnhub is borderline).

**Out:** no automatic promotion (CI-5) and no search (CI-6) — a human reads the table and decides.

## Deliverables

- `Experiment` node + runner + comparison + surface table.
- Tests (100% coverage) with a fixture champion/challenger.

## Acceptance

- `experiment run --champion ingest-champion --challenger ingest-c12-d90` produces a comparison node
  and table showing degradation-rate and fetch-time deltas.
- Re-running aggregates across N trials (variance visible).
- `make ci` green.

## Dependencies

- CI-2 (RunMetrics), CI-3 (ParameterSet). Blocks CI-5.
