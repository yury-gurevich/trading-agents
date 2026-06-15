<!-- Agent: planning | Role: sprint handover -->
# Sprint 38 — Analyst relative strength (benchmark-relative momentum, blended into the technical pillar)

**Status:** shipped · **Branch:** `sprint-38-analyst-relative-strength` · **Build phase:** P11 · **Effort: S–M**

> Implemented directly by the planning agent ("plan next sprint and when happy code it"). Green at the
> full gate; 592 tests, floor 100.00. **One design change from the plan below:** the benchmark is
> fetched in a **separate** provider request (`request_benchmark_bars`), **not** appended to the
> candidate request. Appending it tripped the provider's stale-/missing-ticker gate (the benchmark is
> absent from unit fixtures) → `used_fallback` → the analyst rejected every candidate. A separate,
> fault-tolerant fetch (returns `()` on any fault/absence → RS simply skips) is also the more robust
> design: a missing benchmark forgoes the RS signal instead of halting all analysis. It writes its own
> `MarketSnapshot`, but the lineage assertions traverse *scan* lineage, so they were unaffected. Also
> fixed one stateful test fixture (`ReboundingDataSource`) that counted provider OHLCV calls to time a
> phase switch — it now ignores benchmark-only probes so the extra call doesn't perturb the count.

## Goal

Add a **relative-strength (RS)** signal to the analyst: how a candidate's recent return compares to a
**benchmark** (the S&P 500 via `SPY`) over a trailing window. Per the reference design, RS is **not** a
fourth composite pillar — it is **blended into the technical pillar** at `0.8 · technical + 0.2 · rs`,
because it is a price-performance signal, not a separate evidence class like fundamentals or sentiment.
The composite weights (tech 0.50 / fund 0.30 / sent 0.20) are untouched.

The analyst already requests OHLCV from the provider; this sprint adds the **benchmark ticker** to that
request and computes RS analyst-side — **no contract change** (the benchmark bars ride in the existing
`MarketData.bars`). Designed so that **when benchmark bars are absent/insufficient, RS is skipped and
the technical score is unchanged** → every existing pinned value keeps its number; only new RS-bearing
tests are pinned fresh.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails); `docs/sprints/sprint-31-p11-analyst-oscillators.md`
  (the indicator-module + band-rule convention you mirror).
- **Shipped code you extend (read it):**
  - `agents/analyst/domain/scoring.py` (90L) — `score_candidate(candidate, bars, fundamentals,
    settings)`; `technical = _bounded(raw/100.0)`. You add a `benchmark_bars` argument, compute RS, and
    **blend it into `technical` before the composite**.
  - `agents/analyst/domain/indicators.py` / `technical_rules.py` — the `None`-on-short-history +
    named-band-constant conventions to mirror exactly.
  - `agents/analyst/agent.py` (`_score`, ~line 133; `_window`, ~line 159) — passes per-ticker bars; you
    extract the benchmark's bars once and pass them into each `score_candidate`.
  - `agents/analyst/provider_client.py` (`request_market_data`, ~line 44) — builds the `DataRequest`
    `tickers` from the candidates. You **append the benchmark ticker** so its OHLCV comes back.
  - `agents/analyst/settings.py` (76L) — add the benchmark/RS tunables here.
  - `contracts/analyst.py` — confirm `Recommendation.technical_score` exists (it does); CONTRACT stays
    `0.1.0`, `owns_graph` untouched. RS is folded into `technical_score`; **no new field.**

### The scoring rule (port these bands exactly)

- `compute_relative_strength(stock_bars, benchmark_bars, window) -> float | None`:
  return `stock_return_pct − benchmark_return_pct`, where each is
  `(close[-1] / close[-(window+1)] − 1) · 100` over the trailing `window`. Returns **`None`** when either
  series has `< window + 1` bars or a zero/degenerate base price (mirror the indicators' short-history
  `None`). Never raises.
- `score_relative_strength(rs: float) -> float` — named band constants, first match wins:
  `> 5 → 80`, `> 0 → 60`, `> −5 → 40`, else `20`. (Strict `>`; mirror the band convention in
  `technical_rules.py`.)

### Design decision — RS lives inside the technical pillar (decided; read)

RS blends into the technical score (`0.8 · tech + 0.2 · rs`), **not** the 4-way composite. Rationale: it
keeps the reference blend exactly, leaves the composite pillar weights (and every existing
fundamental/sentiment test) untouched, and reflects that RS is a price signal. **When RS is `None`
(no/short benchmark history) the technical score is the indicator score alone** — identical to today,
so nothing re-pins.

### The blend (inside the technical pillar)

In `score_candidate`, after `technical = _bounded(raw/100.0)`:

- `rs_raw = compute_relative_strength(bars, benchmark_bars, settings.rs_window)`.
- If `rs_raw is None`: `technical` unchanged.
- Else: `rs = _bounded(score_relative_strength(rs_raw) / 100.0)`; then
  `technical = _bounded((1 - settings.relative_strength_weight) * technical + settings.relative_strength_weight * rs)`.
- Put `rs_raw` and the RS sub-score into `metrics` (e.g. `relative_strength`, `rs_score`) only when
  present, so they are auditable. The composite/confidence math downstream is unchanged.

## Part A — Settings

`agents/analyst/settings.py` — add to `AnalystSettings`:

- `benchmark_ticker: str = tunable("SPY", why="Relative-strength benchmark; SPY tracks the S&P 500 universe the scanner targets.")`
- `rs_window: int = tunable(20, why="Reference relative-strength lookback (~one trading month).", ge=2, le=120, unit="bars")`
- `relative_strength_weight: float = tunable(0.20, why="Reference weight of relative strength within the technical pillar (0.8 technical / 0.2 RS).", ge=0.0, le=1.0)`

Keep `settings.py` < 200L.

## Part B — Relative-strength rules

New `agents/analyst/domain/relative_strength.py` — ≤ 120L:

```python
"""Relative-strength signal and its 0-100 band score.

Agent: analyst
Role: compare a candidate's trailing return to a benchmark and band-score the spread.
External I/O: none.
"""
```

- `compute_relative_strength` and `score_relative_strength` exactly as specified (named band constants;
  pure; never raises). A small `_return_pct(bars, window) -> float | None` helper shared by both legs.

## Part C — Fold into scoring

`agents/analyst/domain/scoring.py`:

- Signature → `score_candidate(candidate, bars, fundamentals, benchmark_bars, settings)` (insert
  `benchmark_bars: tuple[OHLCVBar, ...]` before `settings`).
- Apply the technical-pillar blend above. `ScoreBreakdown` needs **no** new field (RS rides inside
  `technical_score`); just enrich `metrics`. The `insufficient_market_history` early return is
  unchanged.

## Part D — Wire the request + agent

- `agents/analyst/provider_client.py`: append the benchmark to the request tickers — e.g.
  `tickers = (*candidate_tickers, settings.benchmark_ticker)` **de-duplicated** (guard against a
  candidate that *is* the benchmark). This needs the analyst settings in `request_market_data`; pass the
  `benchmark_ticker` (or the settings) in from `agent.py` rather than importing settings there.
- `agents/analyst/agent.py` `_score`: `benchmark_bars = bars.get(self._settings.benchmark_ticker, ())`;
  pass it into each `score_candidate`. The benchmark is **reference data, never scored as a candidate**
  (the loop iterates `candidate_set.candidates`, so it is naturally excluded).

## Part E — Tests

### E1. `agents/analyst/tests/test_relative_strength.py` — ≤ 110L

Hand-built bar series: stock outperforms benchmark (RS > 5 → 80), mild out/under-performance across each
band boundary (both sides of `5`, `0`, `−5`), equal performance (RS 0 → 60), short stock or short
benchmark history → `None`, zero/degenerate base price → `None`. Never raises.

### E2. Scoring blend

- New: a candidate **with** benchmark bars → hand-computed blended `technical_score`
  (`0.8 · tech + 0.2 · rs`) and the resulting confidence; `metrics` carries `relative_strength`.
- Existing `score_candidate` call sites gain `benchmark_bars=()` → RS skipped → **every pinned
  technical/confidence value unchanged** (mechanical arg addition only).

### E3. Agent + request + pipeline regression

- The analyst's `DataRequest` now includes `benchmark_ticker` (de-duplicated) — **update any test that
  asserts the exact requested ticker set.**
- An analyst-agent test where `market.bars` includes benchmark bars → a candidate's `technical_score`
  reflects the RS blend.
- Existing analyst-agent and full-pipeline tests use `FakeDataSource` with no benchmark fixture →
  `benchmark_bars == ()` → RS skipped → **no re-pin.** Run the whole suite.

## Coordination note

Sprint 37 (sentiment pillar) **also** inserts a parameter into `score_candidate` (`news`). These two
analyst sprints don't run simultaneously (one active sprint at a time); whichever lands **second**
rebases and adds its parameter alongside the other — a mechanical signature merge, no logic conflict
(both new pillars/signals are independent and both skip cleanly when their input is empty).

## Steps

1. Branch `sprint-38-analyst-relative-strength` off `main`.
2. **A** settings → **B** `relative_strength.py` (+ E1) → **C** blend into `scoring.py`.
3. **D** request + agent wiring. `make ci`.
4. **E2/E3**: add RS-bearing tests; add `benchmark_bars=()` to existing call sites; fix the requested-
   ticker assertion; full-suite regression. `make ci` green at floor 100.00.
5. `wc -l agents/analyst/domain/*.py agents/analyst/settings*.py` — all < 200.
6. Push; hand back.

## Acceptance criteria

- `compute_relative_strength` / `score_relative_strength` reproduce the reference window math and bands
  (hand-verified), return `None` on short/degenerate history, and never raise.
- RS blends into the technical score at the configured weight; when RS is absent the technical score is
  unchanged and **no existing expected value changes**.
- The analyst requests the benchmark ticker (de-duplicated); the benchmark is never scored as a
  candidate. **No contract change** (analyst 0.1.0); **no new dependency**.
- `make ci` green at/above floor 100.00; import-linter kept; every touched/new module < 200L.

## Out of scope

- Beta (scanner) and any RS as a standalone composite pillar; signal-diversity selection; the sentiment
  pillar (S37). Any change outside the analyst package + its tests.

## Handback report (paste into PR / reply)

- Confirm no contract change and that the absent-benchmark path leaves the technical score identical
  (existing values re-used, only the mechanical `benchmark_bars=()` arg added).
- The RS window/bands/weight and one worked example (stock vs benchmark return → RS → blended technical).
- How the benchmark ticker is appended/de-duplicated and excluded from candidate scoring.
- Final line counts: `relative_strength.py`, `scoring.py`, `settings.py`. New coverage % / floor; total
  test count; which requested-ticker assertion was updated.

The planning agent reviews, merges to `main`, and continues P11 (signal-diversity selection; then PM /
scanner / reporter gaps) and P12 (the sentiment trinity).
