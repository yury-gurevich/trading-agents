<!-- Agent: planning | Role: sprint handover -->
# Sprint 34 — Provider fundamentals feed (Finnhub metrics → MarketData.fundamentals)

**Status:** planned · **Branch:** `sprint-34-provider-fundamentals` · **Build phase:** P11 · **Effort: M**

## Goal

Make the provider actually **fetch and return per-ticker fundamental metrics**. The
`MarketData.fundamentals: dict[Ticker, dict[str, float]]` field already exists on the contract but
is **always empty today** — the provider has no fundamentals source and never populates it. This
sprint implements the source + wiring so a `get_market_data` request that asks for the
`"fundamentals"` field comes back with the ~10 metric values the (future) analyst fundamental
scorer needs (P/E, ROE, net margin, current ratio, P/B, debt/equity, EPS growth, revenue growth).

This is the **prerequisite** the build plan flagged: it unblocks the analyst fundamental-scoring
sprint that follows. **No contract schema change** (the field and `DataRequest.fields` entry
already exist) and **no new third-party dependency** (stdlib `urllib` + `json`, exactly like the
existing `StooqDataSource`).

**Explicitly out of scope (separate later slices):** news/sentiment (needs a FinBERT/embeddings ML
stack), the earnings calendar (belongs with the scanner earnings-exclusion gap), and a VIX/FRED
macro feed. This sprint is fundamentals-only.

## Why (context)

- Read first: `docs/sprints/README.md` (the non-negotiable guardrails); `docs/sprints/sprint-04-provider-agent.md` (the original provider/`DataSource` boundary — this sprint extends it the same way).
- **Shipped code you extend (read it):**
  - `agents/provider/sources.py` (140L) — the `DataSource` Protocol + `FakeDataSource` +
    `StooqDataSource`. You add a third port method and implement it on both. `StooqDataSource`
    (urllib download + CSV parse, `_download` marked `# pragma: no cover`, parse tested over a raw
    string) is the **exact pattern** to mirror for the Finnhub source.
  - `agents/provider/agent.py` (118L) — `_get_market_data` fetches `bars` inside a
    `fault_boundary(..., reraise=False)` and builds `MarketData`. You add a fundamentals fetch
    (field-gated, in its own fault boundary) and populate `MarketData.fundamentals`.
  - `agents/provider/domain/integrity.py` — `validate_bars` / `degraded_quality` build the
    `DataQualityTrace`. You do **not** change OHLCV integrity; you add a single degraded-note path
    for fundamentals (see Part D).
  - `agents/provider/settings.py` (87L) — `finnhub_api_key: str = Field(default="", repr=False)`
    **already exists**. Add only the base URL + timeout.
  - `contracts/provider.py` — confirm `MarketData.fundamentals` and `DataRequest.fields`
    (`"fundamentals"` is already documented) are untouched; **CONTRACT stays version 0.1.0**
    (`external_io` already lists `finnhub`).
- **The reference fetch (port faithfully):** the prior system called Finnhub
  `company_basic_financials(ticker, "all")` and read `response["metric"]` — a flat object of metric
  name → number. The analyst then reads these exact keys (with the listed fallbacks):

  | Metric | Finnhub key(s) (first present wins) |
  | --- | --- |
  | P/E | `peBasicExclExtraTTM`, `peTTM` |
  | ROE | `roeTTM` |
  | Net margin | `netProfitMarginTTM` |
  | Current ratio | `currentRatioQuarterly` |
  | P/B | `pbQuarterly`, `pbAnnual` |
  | Debt/Equity | `totalDebt/totalEquityQuarterly`, `totalDebt/totalEquityAnnual` |
  | EPS growth YoY | `epsGrowthTTMYoy` |
  | Revenue growth YoY | `revenueGrowthTTMYoy` |

  The provider emits **all** of these keys (the union, including the fallbacks) so the analyst sprint
  can apply its own fallback logic unchanged. Keep only float-coercible values; drop `None`/missing.

## Part A — Extend the DataSource port

`agents/provider/sources.py`:

- Add to the `DataSource` Protocol:
  ```python
  def fetch_fundamentals(
      self, tickers: tuple[str, ...], window: Window
  ) -> dict[str, dict[str, float]]:
      """Fetch per-ticker fundamental metrics; empty dict per ticker on no data."""
      ...  # pragma: no cover - protocol declaration only.
  ```
  (`window` is taken for signature uniformity with `fetch_ohlcv`; Finnhub's metric endpoint is
  point-in-time and ignores the dates — that's fine.)
- `FakeDataSource`: add a `fundamentals: dict[str, dict[str, float]] = {}` constructor fixture and a
  `fail_fundamentals: bool = False` flag (mirroring `fail_ohlcv`). `fetch_fundamentals` raises
  `RuntimeError("fundamentals source unavailable")` when `fail_fundamentals`, else returns the
  subset of the fixture for the requested tickers.
- `StooqDataSource`: add `fetch_fundamentals(...)` returning `{}` (Stooq has no fundamentals).

Confirm `sources.py` stays < 200L (≈160 after these additions).

## Part B — Finnhub fundamentals source

New `agents/provider/fundamentals.py` — ≤ 95L.

```python
"""Finnhub fundamentals source over the provider DataSource boundary.

Agent: provider
Role: fetch per-ticker key metrics from Finnhub's /stock/metric endpoint (no OHLCV).
External I/O: optional HTTPS calls to finnhub.io.
"""
```

- A module constant tuple `_FUNDAMENTAL_KEYS` holding the union of Finnhub keys in the table above
  (these are fixed API field names — the rule, not tunable policy — so a named constant, mirroring
  how the technical band constants live in their rules modules).
- `class FinnhubDataSource:` taking `api_key: str`, `base_url: str`, `timeout: int` (from settings).
  Implement the **full** `DataSource` port:
  - `fetch_ohlcv(...) -> tuple[OHLCVBar, ...]` → `()` (Finnhub daily candles are premium-only; this
    source is fundamentals-only — combine it with Stooq via Part C).
  - `fetch_regime_inputs(as_of) -> RegimeInputs` → `RegimeInputs(as_of=as_of, vix=None)`.
  - `fetch_fundamentals(tickers, window)` → for each ticker, GET
    `{base_url}/stock/metric?symbol=<T>&metric=all&token=<api_key>`, parse JSON, read the `metric`
    object, extract `_FUNDAMENTAL_KEYS`, coerce each to `float` (drop `None`/non-numeric / a missing
    `metric` object). A ticker with no usable metric is simply absent from the returned dict.
- Keep the network call in a `_download(self, ticker) -> str` helper marked `# pragma: no cover`
  (mirror `StooqDataSource._download`, `urllib.request.urlopen`, hardcoded HTTPS, `noqa: S310`,
  `timeout=`). Put the JSON→`dict[str, float]` extraction in a **pure** module function
  (e.g. `_parse_metrics(raw_json: str) -> dict[str, float]`) so it is unit-tested over a captured
  fixture string with **no network**. Never raise out of `fetch_fundamentals` for a single bad
  ticker — skip it; let a hard transport failure propagate to the agent's fault boundary.

## Part C — Composite source (real wiring)

New `agents/provider/composite.py` — ≤ 45L.

```python
"""Composite DataSource that routes OHLCV/regime and fundamentals to different feeds.

Agent: provider
Role: combine a price/regime source (Stooq) with a fundamentals source (Finnhub).
External I/O: none directly (delegates to the wrapped sources).
"""
```

`class CompositeDataSource:` constructed with `price_source: DataSource` and
`fundamentals_source: DataSource`. `fetch_ohlcv` / `fetch_regime_inputs` delegate to
`price_source`; `fetch_fundamentals` delegates to `fundamentals_source`. This is the realistic
production wiring (`CompositeDataSource(StooqDataSource(), FinnhubDataSource(...))`); the CI gate
still runs entirely on `FakeDataSource`.

## Part D — Agent wiring

`agents/provider/agent.py`, in `_get_market_data`:

- After OHLCV validation builds `bars, quality`, add a **field-gated** fundamentals fetch: only when
  `"fundamentals" in data_request.fields`. Fetch inside a **separate**
  `fault_boundary(..., capability="get_market_data", reraise=False)`; on a captured fault leave
  `fundamentals = {}` and mark the trace degraded:
  `quality = quality.model_copy(update={"notes": quality.notes + ("fundamentals_degraded",), "used_fallback": True})`.
- Pass `fundamentals=fundamentals` into the returned `MarketData(...)`. When the field is not
  requested, `fundamentals` stays `{}` (the contract default) — **no behavior change for existing
  OHLCV-only callers**, so the dispatcher/pipeline fixtures need no re-pin.
- The graph write (`write_market_snapshot`) is **unchanged** — persisting fundamentals as graph
  nodes is out of scope (flag it as a follow-up if you think it's needed; do not add it here).

Confirm `agent.py` stays < 200L (~133 expected).

## Part E — Settings

`agents/provider/settings.py` — add next to the existing `finnhub_api_key`:

- `finnhub_base_url: str` (default `"https://finnhub.io/api/v1"`) — plain `Field`, not a `tunable`
  (it's an endpoint, not a policy knob), mirroring how the Stooq base URL is a class constant.
- `finnhub_timeout: int = tunable(10, why="...", ge=1, le=60, unit="seconds")`.

Keep `settings.py` < 200L.

## Part F — Tests

### F1. `agents/provider/tests/test_sources.py` (extend) + a focused fundamentals test

- `_parse_metrics`: a captured Finnhub JSON fixture string (a realistic `{"metric": {...}, ...}`
  with all target keys plus extras) → the expected `dict[str, float]`; assert non-target keys are
  dropped, `None`/non-numeric values are dropped, and a missing/empty `metric` object → `{}`.
- `FakeDataSource.fetch_fundamentals`: returns the per-ticker subset; `fail_fundamentals=True`
  raises.
- `StooqDataSource.fetch_fundamentals` → `{}`.
- `CompositeDataSource`: `fetch_ohlcv`/`fetch_regime_inputs` hit the price source,
  `fetch_fundamentals` hits the fundamentals source (use two distinct `FakeDataSource`s and assert
  routing).
- Keep the live Finnhub path behind the same env-gated pattern as the Stooq network test (skipped
  by default; no network in CI).

### F2. `agents/provider/tests/test_provider_agent.py` (extend)

- `get_market_data` with `fields=("ohlcv", "fundamentals")` and a `FakeDataSource` carrying
  fundamentals → `MarketData.fundamentals` populated for the requested tickers; OHLCV unchanged.
- `fields=("ohlcv",)` (default) → `MarketData.fundamentals == {}` (proves field-gating; existing
  callers unaffected).
- `fail_fundamentals=True` with the field requested → `fundamentals == {}` **and**
  `"fundamentals_degraded" in quality.notes` and `used_fallback is True`; bars/provenance still
  written normally (the OHLCV path is independent).

### F3. Confirm no regression

Run the whole suite. Existing provider, dispatcher, and pipeline tests use OHLCV-only requests and
must pass **unchanged** (no re-pin expected). The contract single-writer/boundary meta-tests must
stay green (no `owns_graph`/version change).

## Steps

1. Branch `sprint-34-provider-fundamentals` off `main`.
2. **A** port + Fake/Stooq → **B** `fundamentals.py` (+ F1 parse test) → **C** `composite.py` (+ F1 routing).
3. **D** agent wiring → **E** settings. `make ci`.
4. **F2/F3** agent tests + full-suite regression check. `make ci` green at the coverage floor.
5. `wc -l agents/provider/*.py agents/provider/domain/*.py` — all < 200.
6. Push; hand back.

## Acceptance criteria

- `fetch_fundamentals` exists on the port and all three real implementations (Fake/Stooq/Finnhub)
  plus the composite; Finnhub parsing is hand-verified over a fixture and never raises per-ticker.
- A `get_market_data` request including `"fundamentals"` returns the metric dict; a request without
  it returns `{}`; a fundamentals-source failure degrades cleanly (empty + `fundamentals_degraded`
  note) without affecting the OHLCV result or provenance.
- **No contract change** (CONTRACT 0.1.0, `owns_graph` unchanged); **no new dependency**.
- All existing tests pass unchanged; `make ci` green at/above the coverage floor (100.00).
- Import-linter kept; every touched/new module < 200L.

## Out of scope (later sprints)

- **Analyst fundamental scoring** — the next sprint: port `score_fundamental` (8 metrics, threshold
  bands, `data_incomplete` handling) into the analyst as a new pillar, consuming
  `MarketData.fundamentals`. Spec source: memory `v1-deterministic-port-gaps.md`.
- **News + sentiment** (FinBERT/embeddings stack) and the **earnings calendar** (with the scanner
  earnings-exclusion gap) — separate slices.
- **Relative strength** — not actually blocked on a provider change (it only needs benchmark OHLCV,
  which the provider already serves); it is an analyst-side sprint.
- VIX/FRED macro feed; persisting fundamentals to the graph.

## Handback report (paste into PR / reply)

- Confirm CONTRACT unchanged (still 0.1.0, `owns_graph`/`external_io` untouched) and no new
  dependency added.
- The `_FUNDAMENTAL_KEYS` set emitted and how float coercion handles `None`/non-numeric/missing
  `metric`.
- The degraded-path behavior (note added, `used_fallback`, OHLCV unaffected).
- Final line counts: `fundamentals.py`, `composite.py`, `sources.py`, `agent.py`, `settings.py`.
- New coverage % and floor; total test count; confirmation existing tests needed no re-pin.

The planning agent reviews, merges to `main`, and plans the **analyst fundamental-scoring** sprint
that consumes this feed.
