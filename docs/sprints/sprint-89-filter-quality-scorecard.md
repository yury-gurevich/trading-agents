# Sprint 89 — Filter-quality scorecard: the measurement engine (DL-09 part B.1)

**Phase:** P15 / trading-pack — filter-quality measurement (DL-09)
**Branch:** `sprint-89-filter-quality-scorecard`
**Status:** shipped (0.25.00)

---

## Goal

S88 recorded a `FilterVerdict` (decision + features) for every evaluated ticker and added the bypass
counterfactual. This sprint builds the **measurement engine** that turns those verdicts into the
evidence the operator wanted: a per-filter confusion matrix — which filters earn their place, which
throw away winners. Outcomes are **injected** (a fixed-horizon forward return per ticker), matching the
forecaster-scorecard discipline; wiring real outcomes (reference-Postgres forward returns) is the next
slice.

## What shipped — `agents/curator/domain/filter_quality.py`

- **`score_filters(verdicts, outcomes) -> FilterScorecard`** (pure). For each filter, among the tickers
  it dropped (with a known outcome): `good_drops` (dropped & fell), `missed_winners` (dropped & rose),
  and `precision = good_drops / dropped`. Plus the scanner's overall keep quality (`good_keeps` /
  `wrong_keeps` / `keep_precision`). Tickers with no outcome are skipped. **Bypassed drops carry a real
  outcome, so a drop that rose is finally counted as a missed winner — the DL-09 counterfactual made
  measurable.**
- **`collect_verdicts(graph) -> tuple[FilterVerdict, ...]`** reads every recorded verdict off the
  graph's `ScanRun` nodes (via the persisted `CandidateSet.filter_trace.verdicts`).

The confusion matrix realized:

| | rose | fell |
| --- | --- | --- |
| **filter dropped** | missed winner | good drop |
| **scanner kept** | good keep | wrong keep |

## Design notes

- **Outcomes injected, never fetched** — same rule as the forecaster scorecards; keeps the function pure
  and testable, and defers the real-data dependency.
- Lives in the **curator** (the datasets + measurement agent, per DL-09), reading the scanner's
  graph-persisted verdicts — no scanner change.
- `bypassed` does not change scoring: a bypassed ticker's `decision` is still `dropped`, so it lands in
  the drop cells; bypass is just *how* we obtained its outcome.

## Exit criteria

- [x] `score_filters` produces per-filter precision (good drops vs missed winners) + keep quality.
- [x] Bypassed drops that rose are counted as missed winners (the counterfactual).
- [x] `collect_verdicts` reads recorded verdicts off `ScanRun` nodes.
- [x] `make ci` green; 100 % coverage; modules ≤ 200 lines; import-linter unchanged.

## Version bump

New measurement capability → **MINOR**. 0.24.00 → **0.25.00**.

## Next (DL-09 part B.2 — wiring real outcomes)

- **Forward-return outcomes** from the reference Postgres (price_cache OHLCV): look up each verdict
  ticker's return over a fixed horizon from its scan date → feed `score_filters` real ground truth.
- **Curator capability + `assemble_filter_examples`**: expose the scorecard as a curator capability and
  emit `ExampleRecord`s (content = features, label = outcome) into the existing
  Dataset/Manifest/Predictor loop.
- Optional: a CLI/surface to print the scorecard, and persist it as a graph artifact.
