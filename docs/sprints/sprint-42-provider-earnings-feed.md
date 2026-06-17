<!-- Agent: planning | Role: sprint handover -->
# Sprint 42 — Provider earnings-calendar feed (P11, unblocks the scanner earnings-window exclusion)

**Status:** ✅ shipped (2026-06-18, on `main`) · **Build phase:** P11 · **Effort: M** · executed directly (no coding agent this cycle)

> **Handback (shipped).** Built as scoped, provider-only. `DataSource.fetch_earnings(tickers, window)`
> added to the Protocol + `FakeDataSource` (fixture + `fail_earnings`); real
> `FinnhubDataSource.fetch_earnings` (`/calendar/earnings`, `_download_earnings` `# pragma: no cover`,
> `earnings_lookahead_days` init param) via a pure `_parse_next_earnings(raw, on_or_after)` (earliest
> ISO date ≥ as-of; never raises) + `_parse_iso_date` helper, both in `fundamentals_parse.py`; stubs on
> tiingo/stooq/fmp/av_sentiment + the orchestration double; composite delegates to Finnhub and threads
> `finnhub_earnings_lookahead_days`. Agent field-gates `"earnings_calendar"` →
> `MarketData.earnings` (degrade-to-empty + `"earnings_degraded"` note + `used_fallback`, twin of
> news/sectors). CONTRACT `0.3.0 → 0.4.0`; `external_io` unchanged; **boundary meta-test green; no
> other agent changed**. **Refactor:** the four existing field-gates + the new one were extracted from
> `agent.py` into a new focused `market_fields.py` (`collect_optional_fields` + a PEP-695-generic
> `_fetch_optional`) — behaviour-preserving (existing fundamentals/news/sentiment/sectors tests stayed
> green) and it dropped provider `agent.py` **197 → 131L**. `make ci` green: **726 passed, 4 skipped,
> 100.00% coverage**; every module < 200L (`market_fields.py` 135, `sources.py` 182). **Next: the
> scanner earnings-window exclusion consumes `MarketData.earnings`.**

## Goal

Add a **per-ticker next-earnings-date feed** to the provider:
`DataSource.fetch_earnings(tickers, window) -> dict[Ticker, date]`, served live by **Finnhub
`/calendar/earnings`**, **field-gated** into a new `MarketData.earnings` on the request field
`"earnings_calendar"`. This is the data substrate the **scanner earnings-window exclusion** (the
next P11 sprint) needs — an earnings date is **market reference data**, so by the one rule it must
come from the provider (the single data boundary), never be owned by the scanner.

**One agent at a time (build-plan principle):** this sprint is entirely inside the **provider**. The
scanner gate that consumes `MarketData.earnings` is a separate, follow-on sprint. This mirrors how
every feed shipped before its consumer (S34 fundamentals→S35; S36 news→S37; S47 sentiment→S48;
S51 sectors→S52).

## Why (context)

- **Exact pattern to mirror: Sprint 51 (`docs/sprints/sprint-51-provider-sector-feed.md`)** — added
  `fetch_sectors` across every `DataSource`, field-gated `"sectors"` → `MarketData.sectors`, bumped the
  provider CONTRACT. This sprint is the twin for `earnings`.
- The **real fetch** mirrors `agents/provider/fundamentals.py::fetch_news` (per-ticker loop, the
  `_download_*` is `# pragma: no cover`, the pure parser is tested offline via a `MethodType` stub).
- `external_io` is **unchanged**: Finnhub is already the provider's fundamentals/news/sectors source.
- `DataRequest.fields` already documents `earnings_calendar` (no docstring change needed).
- **Module-budget note:** provider `agent.py` is at **197L**. Adding a fifth field-gate block inline
  would breach the 200L hard limit, so this sprint **extracts the repeated field-gate pattern** into a
  generic `_fetch_optional` helper — which nets `agent.py` *smaller* while making the earnings gate a
  4-line call. All four existing field-gates (fundamentals/news/sentiment/sectors) route through it.

## Parts

- **A — `agents/provider/sources.py`**: add `fetch_earnings(self, tickers, window) -> dict[str, date]`
  to the `DataSource` Protocol (`...  # pragma: no cover`). `FakeDataSource`: `__init__` gains
  `earnings: dict[str, date] | None = None` and `fail_earnings: bool = False`; `fetch_earnings`
  returns the fixture subset for requested tickers (raise on `fail_earnings`), mirroring `fetch_sectors`.
- **B — the other `DataSource` impls** (stub `return {}`, mirror their `fetch_sectors` stub, window
  arg `# noqa: ARG002`): `tiingo.py`, `stooq.py`, `fmp.py`, `av_sentiment.py`, and the orchestration
  double `orchestration/tests/helpers.py::ReboundingDataSource`.
- **C — `agents/provider/fundamentals.py` (`FinnhubDataSource`)**: the **real** `fetch_earnings` —
  `__init__` gains `earnings_lookahead_days: int = 30`; loop tickers, `_download_earnings(ticker,
  from_date, to_date)` (`# pragma: no cover`, `/calendar/earnings?from=&to=&symbol=&token=`), parse via
  a pure `_parse_next_earnings(raw_json, on_or_after) -> date | None`; `from = window.end`,
  `to = window.end + lookahead`; include a ticker only when a next date is found.
- **D — `agents/provider/fundamentals_parse.py`**: pure `_parse_next_earnings(raw_json, on_or_after)`
  — parse `earningsCalendar` array, collect ISO `date` strings `>= on_or_after`, return the **earliest**;
  never raises → `None` on any malformed/empty payload or no upcoming date.
- **E — `agents/provider/composite.py`**: `CompositeDataSource.fetch_earnings` delegates to the
  `fundamentals_source` (Finnhub); `market_source_from_settings` passes
  `earnings_lookahead_days=settings.finnhub_earnings_lookahead_days` into `FinnhubDataSource`.
- **F — `agents/provider/agent.py`**: extract `_fetch_optional(requested, fetch, empty, note, quality)`
  generic helper; route all five optional fields (fundamentals, news, sentiment, sectors, **earnings**)
  through it; field-gate `"earnings_calendar"` (degrade note `"earnings_degraded"`); pass
  `earnings=earnings` to `MarketData(...)`.
- **G — `contracts/provider.py`**: `MarketData.earnings: dict[Ticker, date] = Field(default_factory=dict)`
  with a one-line doc; bump provider CONTRACT `0.3.0 → 0.4.0`. `external_io` unchanged.
- **H — `agents/provider/settings.py`**: `finnhub_earnings_lookahead_days` tunable (30, ge 1 le 180,
  unit days, why="forward window scanned for each ticker's next earnings date").

## Part T — Tests (every branch; 100% floor holds)

- `FakeDataSource.fetch_earnings`: returns the fixture subset; `fail_earnings=True` raises.
- `_parse_next_earnings` known-value: a calendar with two future dates → the earliest; a past-only
  calendar → `None`; missing/empty/non-dict/non-list/bad-date payload → `None`; a date exactly on
  `on_or_after` → included.
- `FinnhubDataSource.fetch_earnings` loop covered by stubbing `_download_earnings` with a `MethodType`
  returning canned JSON for one ticker and `{}`/skip for another (mirror the fundamentals offline test).
- Provider agent: a `get_market_data` request with `fields=("earnings_calendar",)` returns
  `MarketData.earnings` populated from a `FakeDataSource(earnings=…)`; a `fail_earnings=True` source
  degrades to `earnings={}` with the `"earnings_degraded"` note + `used_fallback=True`. Confirm the
  `_fetch_optional` extraction left the existing fundamentals/news/sentiment/sectors degrade behaviour
  byte-identical (their existing agent tests stay green untouched).
- Regression: every existing caller (scanner/analyst/PM) does **not** request `"earnings_calendar"` →
  `earnings == {}`, no degradation → untouched. Run the whole suite.

## Acceptance criteria

- The provider serves `MarketData.earnings` (per-ticker next earnings date) when `"earnings_calendar"`
  is requested, live via Finnhub, field-gated with the same degrade-to-empty + quality-note semantics
  as news/sectors.
- Provider CONTRACT `0.4.0`; `external_io` unchanged; boundary meta-test green. No other agent changed.
- The `_fetch_optional` extraction is behaviour-preserving for the four existing fields. `make ci`
  green at floor 100.00; every module < 200L.

## Out of scope (the immediate next sprint)

- **Scanner earnings-window exclusion** (the consumer): request `"earnings_calendar"`, drop candidates
  whose next earnings is within `earnings_exclusion_days` of the scan as-of — its own scanner-only sprint.
- A **live earnings probe** (DEP-FEED) — optional follow-up, like the planned sector probe.

## Handback report

- Confirm: provider-only change; CONTRACT `0.4.0`; `external_io` unchanged; field-gate degrade
  semantics match news/sectors; existing callers untouched (`earnings == {}`); the `_fetch_optional`
  refactor preserved the four existing fields. New/changed module line counts; coverage %; test count.
