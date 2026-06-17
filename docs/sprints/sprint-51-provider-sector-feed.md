<!-- Agent: planning | Role: sprint handover -->
# Sprint 51 — Provider sector feed (P11, unblocks the PM sector cap)

**Status:** in progress · **Branch:** `sprint-51-provider-sector-feed` · **Build phase:** P11 (decision-logic depth — the data substrate for the PM sector-concentration cap) · **Effort: M**

## Goal

Add a **per-ticker sector feed** to the provider: `DataSource.fetch_sectors(tickers) -> dict[Ticker, str]`,
served live by **Finnhub `/stock/profile2`** (`finnhubIndustry`), **field-gated** into a new
`MarketData.sectors`. This is the data substrate the **PM sector-concentration cap** (the next P11 sprint)
needs — sector is **market reference data**, so by the one rule it must come from the provider (the data
boundary), never be owned by the PM. It also seeds the **P13** sector-contagion layer.

**One agent at a time (build-plan principle):** this sprint is entirely inside the **provider**. The PM
sector cap that consumes `MarketData.sectors` is a separate, follow-on sprint. This mirrors how every other
feed shipped before its consumer (S34 fundamentals→S35; S36 news→S37; S47 sentiment→S48).

## Why (context)

- **Exact pattern to mirror: Sprint 47 (`docs/sprints/sprint-47-provider-sentiment-feed.md`)** — it added
  `fetch_sentiment` across every `DataSource`, field-gated `"sentiment"` → `MarketData.sentiment`, and
  bumped the provider CONTRACT. This sprint is the twin for `sectors`.
- The **real fetch** mirrors `agents/provider/fundamentals.py::fetch_fundamentals` /`fetch_news`
  (per-ticker loop, `_download_*` is `# pragma: no cover`, the pure parser is tested offline via a
  `MethodType` stub of the download).
- `external_io` is **unchanged**: Finnhub is already the provider's fundamentals/news source — no new
  external system, no boundary-map change.

## Parts

- **A — `agents/provider/sources.py`**: add `fetch_sectors(self, tickers: tuple[str, ...]) -> dict[str,
  str]` to the `DataSource` Protocol (`...  # pragma: no cover`). `FakeDataSource`: `__init__` gains
  `sectors: dict[str, str] | None = None` and `fail_sectors: bool = False`; `fetch_sectors` returns the
  fixture subset for requested tickers (raise on `fail_sectors`), mirroring `fetch_sentiment`. (Watch the
  200-line budget — sources.py is ~141L, fine.)
- **B — the other `DataSource` impls** (stub `return {}`, mirror their `fetch_sentiment` stub):
  `agents/provider/tiingo.py`, `agents/provider/stooq.py`, `agents/provider/fmp.py`,
  `agents/provider/av_sentiment.py`, and the orchestration test double
  `orchestration/tests/helpers.py::ReboundingDataSource`.
- **C — `agents/provider/fundamentals.py` (`FinnhubDataSource`)**: the **real** `fetch_sectors` — loop
  tickers, `_download_profile(ticker)` (`# pragma: no cover`, `/stock/profile2?symbol=…&token=…`), parse
  via a pure `_parse_sector(raw_json) -> str | None` (`finnhubIndustry` when a non-empty string; never
  raises → `None` on any malformed/empty payload); include a ticker only when a sector is found.
- **D — `agents/provider/composite.py`**: `CompositeDataSource.fetch_sectors` delegates to the
  `fundamentals_source` (Finnhub), mirroring `fetch_news`/`fetch_fundamentals`.
- **E — `agents/provider/agent.py`**: field-gate `"sectors"` in `_get_market_data` (twin of the `news`
  block): own `fault_boundary`, on fault `sectors = {}` + a `"sectors_degraded"` quality note +
  `used_fallback=True`; pass `sectors=sectors` to `MarketData(...)`.
- **F — `contracts/provider.py`**: `MarketData.sectors: dict[Ticker, str] = Field(default_factory=dict)`
  with a one-line doc; add `sectors` to the `DataRequest.fields` docstring; bump provider CONTRACT
  `0.2.0 → 0.3.0`. `external_io` unchanged (Finnhub already owned). If any test pins the provider version,
  update it.

## Part T — Tests (every branch; 100% floor holds)

- `FakeDataSource.fetch_sectors`: returns the fixture subset; `fail_sectors=True` raises (mirror the
  sentiment fixture tests).
- `FinnhubDataSource`: `_parse_sector` known-value (valid `finnhubIndustry` → the string; missing/empty/
  non-dict/non-string → `None`); `fetch_sectors` loop covered by stubbing `_download_profile` with a
  `MethodType` returning canned JSON for one ticker and `{}`/skip for another (mirror the existing
  fundamentals offline test).
- Provider agent: a `get_market_data` request with `fields=("sectors",)` returns `MarketData.sectors`
  populated from a `FakeDataSource(sectors=…)`; a `fail_sectors=True` source degrades to `sectors={}` with
  the `"sectors_degraded"` note + `used_fallback=True` (twin of the news-degraded test).
- Regression: every existing caller (scanner/analyst/PM) does **not** request `"sectors"` → `sectors == {}`
  and no degradation → untouched. Run the whole suite. Confirm the new `fetch_sectors` stubs satisfy mypy
  across all sources + the orchestration double.

## Acceptance criteria

- The provider serves `MarketData.sectors` (per-ticker sector string) when `"sectors"` is requested, live
  via Finnhub, field-gated with the same degrade-to-empty + quality-note semantics as news/sentiment.
- Provider CONTRACT `0.3.0`; `external_io` unchanged; boundary meta-test green. No other agent changed.
  `make ci` green at floor 100.00; every module < 200L.

## Out of scope (the immediate next sprints)

- **PM sector-concentration cap** (the consumer): request `"sectors"`, track per-sector deployed value
  while approving orders, reject those breaching `max_sector_pct` — its own single-agent P11 sprint.
- A **live sector probe** (DEP-FEED-03) — optional follow-up, like the S47 sentiment probe.
- **P13** sector-contagion graph edges built on this sector data.

## Handback report (paste into PR / reply)

- Confirm: provider-only change; CONTRACT `0.3.0`; `external_io` unchanged; the field-gate degrade
  semantics match news/sentiment; existing callers untouched (`sectors == {}`). New/changed module line
  counts; coverage % + floor; total test count.
