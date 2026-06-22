# Sprint 88 — Filter decisions as training data: the collection side (DL-09 part A)

**Phase:** P15 / trading-pack — filter-quality measurement (DL-09)
**Branch:** `sprint-88-filter-verdicts-collection`
**Status:** shipped (0.24.00)

---

## Goal

Start turning the scanner's filter decisions into a labeled training source (the operator's
"two-million-dollar question"). Today a dropped ticker vanishes into a bare counter
(`dropped_by_filter: {min_relative_strength: 1}`) — no per-ticker features, no way to score the
filter later. DL-09 needs (a) a per-ticker verdict with the features judged, and (b) a way to observe
what a *dropped* ticker would have done. This sprint ships **the collection side**; the measurement
side (curator assembler + per-filter confusion matrix) and the dual outcome labels come next.

## What shipped

- **`contracts/scanner.py::FilterVerdict`** — `(ticker, decision: survived|dropped, filter_fired,
  features: dict[str,float], bypassed)`. Carried on `FilterTrace.verdicts` (additive, default empty),
  so it rides the existing `CandidateSet` already persisted on `ScanRun`. **scanner CONTRACT 0.1.0 →
  0.2.0** (additive).
- **`ScannerSettings.bypass_scanner_filter`** (bool, default False) — the counterfactual switch.
- **`agents/scanner/domain/filters.py`** reworked: every evaluated ticker now gets a `FilterVerdict`
  with the features the filters judged (price, volume, relative_strength, beta, days_to_earnings) and
  the first filter that would drop it. When `bypass_scanner_filter` is on, a would-be-dropped ticker is
  still emitted as a survivor (so it flows analyst→PM→… and its outcome can later be observed), but its
  verdict still records the real drop + `bypassed=True`. Gate logic split into `_features` +
  `_evaluate` (first-failing-filter + gates-passed); survivor output is byte-for-byte unchanged for
  real survivors (all 34 existing scanner tests pass).

## Design notes

- **Verdicts persist for free.** They live on `FilterTrace` inside `CandidateSet`, which the scanner
  already writes to its `ScanRun` node — no new graph writes.
- **`missing_history` is never bypassed** — a ticker with <2 bars has no features to compute, so bypass
  cannot rescue it.
- **Dual labels are deferred.** The verdict captures the *input* (features + decision) at scan time;
  the *labels* (raw forward return + full-pipeline trade outcome) are attached by the measurement side,
  which matches verdicts to downstream outcomes via the provenance graph.

## Exit criteria

- [x] Every evaluated ticker gets a `FilterVerdict` (decision + filter_fired + features) on `ScanRun`.
- [x] `bypass_scanner_filter` emits dropped tickers as survivors, tagged `bypassed`, while the verdict
      records the real drop and the drop is still counted.
- [x] Existing survivor output (survived_filters + metrics) unchanged; all scanner tests pass.
- [x] `make ci` green; 100 % coverage; modules ≤ 200 lines; import-linter unchanged.

## Version bump

New capability (per-ticker verdict collection + bypass) → **MINOR**. 0.23.04 → **0.24.00**.

## Next (DL-09 part B — measurement)

- **Dual outcome labels**: walk the provenance graph from each bypassed verdict to its realized result —
  (a) raw forward return over a fixed horizon, (b) full-pipeline trade outcome (close trigger).
- **Curator filter-example assembler** (`assemble_filter_examples`) feeding the existing
  ExampleRecord → DatasetManifest → Predictor loop.
- **Per-filter confusion matrix** (dropped×down / dropped×up / kept×up / kept×down) → precision +
  miss-rate per filter — the deterministic evidence.
- Optional: surface verdict counts in `batch_trace`.
