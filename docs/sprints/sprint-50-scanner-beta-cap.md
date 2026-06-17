<!-- Agent: planning | Role: sprint handover -->
# Sprint 50 — Scanner beta computation + beta-cap filter (P11)

**Status:** shipped (2026-06-17, commit `51ee2b6`) · **Branch:** `sprint-50-scanner-beta-cap` · **Build phase:** P11 (decision-logic depth — scanner side) · **Effort: M**

> **Handback (shipped).** Built as scoped. New: `domain/beta.py` (55L, pure `compute_beta` via
> `statistics.variance`/`covariance` over aligned daily returns), `provider_client.py` (79L — extracted
> `request_market_data` out of `agent.py` + added the isolated `request_benchmark_bars`). `agent.py`
> dropped 184→**162L**; `filters.py` 84→99L. **No contract change** (Candidate already carries `metrics`);
> **no boundary-map change**. The beta-cap is the chain's last gate and **purely additive + dormant on thin
> history** — every existing scanner + orchestration test passed untouched (2-bar fixtures → beta `None` →
> no `max_beta` drops). `make ci` green: **688 passed, 4 skipped, 100.00% coverage**; every module < 200L.
> Design note: beta uses the **scan window** (a separate longer beta window is a future tunable/refinement,
> not a second fetch), and only gates when there are ≥ `beta_min_observations` aligned returns.

## Goal

Add the scanner's **beta computation + beta-cap filter** (the named P11 scanner item). The scanner fetches a
**benchmark** price series (fault-tolerant, in isolation — mirrors the analyst's S38 relative-strength
fetch), computes each surviving candidate's **beta** (systematic risk vs the benchmark) as a pure
deterministic function, and **drops candidates whose beta exceeds `max_beta`**. Beta is recorded in the
candidate metrics and the drop is attributed in the filter trace.

**Purely additive + dormant on thin history.** Beta needs enough *aligned* return observations; with the
scanner's short default window (and all existing/orchestration fixtures: 2 bars/ticker → 1 return) beta is
`None`, the beta-cap is **skipped**, and nothing changes — so every existing scanner + pipeline test stays
green untouched. The filter only fires when there is sufficient overlapping history (a longer window, or
the new tests' fixtures).

## Why (context)

- `docs/build-plan.md` §P11 lists "Scanner — beta computation + beta-cap filter; earnings-window exclusion."
  This sprint does the **beta** half (earnings-window stays out of scope — it needs an earnings-calendar
  feed). P11 status line should gain "scanner beta-cap" on closeout.
- **Patterns to mirror (read them):**
  - `agents/analyst/provider_client.py::request_benchmark_bars` — the **isolated, fault-tolerant**
    benchmark fetch (`fields=("ohlcv",)`, returns `()` on any fault so a missing benchmark never degrades
    candidate data — it only forgoes the signal). The scanner gets the same helper.
  - `agents/analyst/agent.py` — how the analyst threads `benchmark_bars` through scoring; the scanner
    threads it through `apply_filters`.
  - `agents/scanner/domain/filters.py::apply_filters` — the deterministic filter chain the beta-cap joins
    (last, after relative strength, so price/volume/RS keep clearer drop attribution).

## Parts

- **A — `agents/scanner/provider_client.py`** (new): extract the scanner's bus request to provider into
  `request_market_data(bus, sink, tickers, window) -> MarketData | None` (move `_request_market_data` out of
  `agent.py` verbatim — keeps `agent.py` < 200L) and add
  `request_benchmark_bars(bus, sink, benchmark_ticker, window) -> tuple[OHLCVBar, ...]` (twin of the
  analyst's: own `fault_boundary`, `fields=("ohlcv",)`, `()` on fault). Fault module strings become
  `agents.scanner.provider_client`. (Existing agent tests still cover `request_market_data`; the
  degraded-path fault asserted in `test_degraded_provider...` is from `_record_provider_degraded`, which
  stays in `agent.py`.)
- **B — `agents/scanner/domain/beta.py`** (new, pure): `compute_beta(stock_bars, benchmark_bars,
  min_observations) -> float | None`. Align closes by date, take simple daily returns over the common
  dates, `beta = cov(stock, benchmark) / var(benchmark)`; return `None` when fewer than `min_observations`
  aligned returns or when benchmark variance is 0 (flat → undefined). Known-value unit tests.
- **C — `agents/scanner/domain/filters.py`**: `apply_filters(tickers, bars, benchmark_bars, settings)` — after
  a ticker clears price/volume/RS, compute its beta; if `beta is not None and beta > settings.max_beta`,
  drop it (`drops["max_beta"] += 1`, attributed) and **do not** add it as a survivor; otherwise keep it,
  adding `"beta"` to `metrics` when computed and `"max_beta"` to `survived_filters` when the gate actually
  applied (beta `None` → gate skipped → neither added, so thin-history fixtures are unchanged).
- **D — `agents/scanner/agent.py`**: use `provider_client.request_market_data`; fetch
  `request_benchmark_bars(...)`; pass `benchmark_bars` into `apply_filters`. Extend `_explain_filter`'s
  text + `_scan_explanation` to mention the beta cap.
- **E — `agents/scanner/settings.py`**: add `benchmark_ticker: str = "SPY"` (identity, not a tunable);
  `max_beta` tunable (e.g. `2.5`, why="exclude names whose systematic risk exceeds the cap", ge 0 le 10);
  `beta_min_observations` tunable (e.g. `3`, ge 2 le 252).

## Part T — Tests (every branch; 100% floor holds)

- `test_scanner_beta.py` (domain): `compute_beta` — a 1:1 series → ~1.0; a 2:1 series → ~2.0; insufficient
  overlap → `None`; flat benchmark (zero variance) → `None`. Filter: a longer-history fixture where one
  ticker is high-beta → **dropped** (`dropped_by_filter["max_beta"] == 1`, `"max_beta"` not in its filters)
  and a low-beta ticker → kept with `metrics["beta"]` set and `"max_beta"` in `survived_filters`; a
  thin-history ticker → beta skipped (kept on the core filters, no `"beta"` metric).
- `test_scanner_agent_beta.py` (agent end-to-end): wire provider with candidate + benchmark bars over a
  longer window; assert the scan drops the high-beta name (in `dropped_by_filter`) and the surviving
  candidate carries `metrics["beta"]`; the benchmark is fetched in isolation. Plus one direct
  `request_benchmark_bars` fault test (no provider registered → `()`), covering the helper's fault branch.
- Regression: the existing `test_scanner_agent.py` + orchestration pipeline tests are unchanged (2-bar
  fixtures → beta `None` → no `max_beta` drops, original `survived_filters` and `dropped_by_filter` exact
  dicts intact). Run the whole suite.

## Acceptance criteria

- The scanner fetches a benchmark in isolation, computes beta deterministically, and drops candidates with
  `beta > max_beta`, attributing the drop in the filter trace; surviving candidates carry their beta metric.
- A missing/degraded benchmark never degrades candidate quality (beta simply skipped). No contract change
  (Candidate already carries a `metrics` dict; `CandidateSet`/`FilterTrace` unchanged); no boundary-map
  change. `make ci` green at floor 100.00; every module < 200L.

## Out of scope

- The scanner **earnings-window exclusion** (needs an earnings-calendar provider feed) — a later P11 item.
- A separate, longer dedicated **beta window** (beta here uses the scan window; extending it is a tunable
  bump or a future refinement — note it, don't build a second fetch).

## Handback report (paste into PR / reply)

- Confirm no contract/boundary change; that existing scanner + pipeline tests are untouched (beta dormant
  on thin fixtures); the `provider_client` extraction kept `agent.py` < 200L. New module line counts;
  coverage % + floor; total test count.
