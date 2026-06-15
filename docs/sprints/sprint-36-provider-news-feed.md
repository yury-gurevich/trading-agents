<!-- Agent: planning | Role: sprint handover -->
# Sprint 36 — Provider news feed (per-ticker headlines into MarketData.news)

**Status:** shipped · **Branch:** `sprint-36-provider-news-feed` · **Build phase:** P11 · **Effort: M**

## Goal

The provider should populate the previously-always-empty `MarketData.news`. Add a `fetch_news`
fetch to the `DataSource` boundary, implement it against Finnhub's `/company-news` endpoint, and
field-gate it in `get_market_data` exactly as Sprint 34 did for fundamentals. The result is a
per-ticker tuple of recent **headline strings** — the raw material the next sprint scores into the
analyst's third (sentiment) pillar.

The provider contract already declares `MarketData.news: dict[Ticker, tuple[str, ...]]` and already
lists `news` as a valid `DataRequest.fields` value, so this is **no contract change** — only the
implementation behind the field. This sprint is deliberately the structural twin of Sprint 34
(provider fundamentals); read that handover first.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails); `docs/sprints/sprint-34-provider-fundamentals.md`
  (the sprint this mirrors almost line for line — same fault-boundary, field-gating, and
  composite-routing shape).
- **Shipped code you extend (read it):**
  - `contracts/provider.py` — `MarketData.news: dict[Ticker, tuple[str, ...]]` (line ~60) and the
    `DataRequest.fields` docstring already name `news`. Confirm both; CONTRACT version and
    `owns_graph`/`external_io` stay **untouched**.
  - `agents/provider/sources.py` — the `DataSource` Protocol (add `fetch_news`), `FakeDataSource`
    (add a `news` fixture + `fail_news`), `StooqDataSource` (`fetch_news` → `{}`). Mirror exactly how
    `fetch_fundamentals` was added across these three in S34.
  - `agents/provider/fundamentals.py` — the `FinnhubDataSource` you extend: it already holds the
    `api_key`/`base_url`/`timeout` and the stdlib-`urllib` download pattern. Add `fetch_news` +
    `_download_news` + a pure `_parse_news` here (or a sibling `news.py` if it would push the file
    over ~160L — prefer a new `agents/provider/news.py` to keep each file focused and < 200L).
  - `agents/provider/composite.py` — `CompositeDataSource` already routes fundamentals → the
    Finnhub source. Add a `fetch_news` that routes to the **same** fundamentals source (Finnhub
    serves both); the price source (Stooq) keeps OHLCV/regime.
  - `agents/provider/agent.py` — `_get_market_data` (line ~58). Add a `news` block that mirrors the
    `fundamentals` block verbatim: field-gated on `"news" in data_request.fields`, fetched inside its
    **own** `fault_boundary(reraise=False)`; on fault → empty `{}` + a `"news_degraded"` quality note
    - `used_fallback=True`. Populate `MarketData(news=...)`.
  - `agents/provider/settings.py` — Finnhub config already present (`finnhub_base_url`,
    `finnhub_api_key`, `finnhub_timeout`). Add the two news tunables in Part A. Keep < 200L (file is
    at 96L — plenty of room).

### The Finnhub call (port this shape)

`/company-news` takes `symbol`, `from`, and `to` (ISO `YYYY-MM-DD`) and returns a JSON **array** of
article objects, each with a `headline` string (plus `summary`, `datetime`, `source`, `url` we do
not need). The contract types news as headline strings, so this sprint extracts **`headline` only**.

`fetch_news(tickers, window) -> dict[str, tuple[str, ...]]`:

- News window is **recent**, not the full OHLCV lookback: `to = window.end`,
  `from = window.end - finnhub_news_lookback_days`. (The analyst requests a 260-day OHLCV window;
  scoring sentiment over 260 days of headlines is wrong — use a short trailing window.)
- Per ticker: download, parse, take the first `max_news_per_ticker` headlines (Finnhub returns
  newest-first); coerce each to `str`, drop empty/missing/non-string headlines. Skip a ticker
  entirely when it yields no usable headline (no empty-tuple entries — mirror how `fetch_fundamentals`
  skips tickers with no usable metric).
- Never raises out of the pure parser. `_download_news` is `# pragma: no cover` (live HTTPS), exactly
  like `_download` in `fundamentals.py`.

## Part A — Settings

`agents/provider/settings.py` — add to `ProviderSettings`:

- `finnhub_news_lookback_days: int = tunable(7, why="Trailing window of company news to fetch; recent headlines only, not the full OHLCV lookback.", ge=1, le=90, unit="days")`
- `max_news_per_ticker: int = tunable(20, why="Cap headlines per ticker so a noisy feed cannot dominate the downstream sentiment pillar.", ge=1, le=100)`

## Part B — News source

New `agents/provider/news.py` — ≤ 160L (keeps `fundamentals.py` and `news.py` each focused):

```python
"""Finnhub company-news source over the provider DataSource boundary.

Agent: provider
Role: fetch recent per-ticker headlines from Finnhub's /company-news endpoint.
External I/O: optional HTTPS calls to finnhub.io.
"""
```

- `FinnhubNewsSource` (or extend `FinnhubDataSource` if you keep it in one file — your call, but
  the boundary methods `fetch_ohlcv`/`fetch_regime_inputs`/`fetch_fundamentals` must all still exist
  on whatever object the composite wraps for news). Constructor takes `api_key`/`base_url`/`timeout`
  like the fundamentals source.
- `fetch_news` as specified above; `_download_news` (`# pragma: no cover`); pure `_parse_news(raw_json,
  cap) -> tuple[str, ...]` extracting/trimming headlines. The non-news boundary methods return the
  empty defaults (`fetch_ohlcv` → `()`, `fetch_regime_inputs` → `RegimeInputs(as_of, vix=None)`,
  `fetch_fundamentals` → `{}`) so the type still satisfies `DataSource` if used standalone.

> Note on the wiring: the existing `CompositeDataSource` takes one `fundamentals_source` and routes
> both fundamentals and (now) news to it. So the simplest path is to **add `fetch_news` to the
> existing `FinnhubDataSource`** (it already implements `fetch_fundamentals`) rather than a second
> object — then the composite's `fundamentals_source` serves both. Choose that unless it pushes
> `fundamentals.py` over the size warn band; if it does, split the Finnhub client across two files but
> keep a single class. Document the choice in the handback.

## Part C — Port + fakes

`agents/provider/sources.py`:

- Add to the `DataSource` Protocol:
  `def fetch_news(self, tickers: tuple[str, ...], window: Window) -> dict[str, tuple[str, ...]]: ...`
  with the protocol-declaration `# pragma: no cover` line.
- `FakeDataSource`: add `news: dict[str, tuple[str, ...]] | None = None` and `fail_news: bool = False`
  constructor args; implement `fetch_news` to return the requested tickers' fixture headlines (or
  raise `RuntimeError("news source unavailable")` when `fail_news`) — mirror `fetch_fundamentals`.
- `StooqDataSource`: `fetch_news` → `{}` (Stooq serves OHLCV only), with the same `noqa: ARG002`
  port-signature comments the sibling stubs use.

## Part D — Composite routing

`agents/provider/composite.py` — add:

```python
def fetch_news(
    self, tickers: tuple[str, ...], window: Window
) -> dict[str, tuple[str, ...]]:
    """Delegate news fetches to the fundamentals (Finnhub) source."""
    return self._fundamentals_source.fetch_news(tickers, window)
```

## Part E — Agent field-gating

`agents/provider/agent.py::_get_market_data` — after the fundamentals block, add the twin news block:

```python
news: dict[str, tuple[str, ...]] = {}
if "news" in data_request.fields:
    with fault_boundary(
        self.sink,
        agent="provider",
        module="agents.provider.agent",
        capability="get_market_data",
        reraise=False,
    ) as ncapture:
        news = self._source.fetch_news(
            data_request.tickers, data_request.window
        )
    if ncapture.fault is not None:
        news = {}
        quality = quality.model_copy(
            update={
                "notes": (*quality.notes, "news_degraded"),
                "used_fallback": True,
            }
        )
```

Pass `news=news` to the returned `MarketData(...)`. **Do not** write news to the graph — like
fundamentals, it rides on `MarketData` for the analyst and is not persisted this sprint
(`write_market_snapshot` is unchanged). If the added block pushes `agent.py` toward the size warn
band, extract the fundamentals+news field-fetch into a small `_fetch_extras` helper (or a
`domain/extras.py`) rather than growing the method.

## Part F — Tests

### F1. `agents/provider/tests/test_news_source.py` — ≤ 130L

Hand-built Finnhub `/company-news` JSON fixtures (pure `_parse_news`, no network):

- A normal array → headlines extracted in order; `max_news_per_ticker` cap trims a long array.
- Missing/empty/non-string `headline` fields dropped; a ticker with no usable headline omitted.
- Malformed payloads (non-array, non-dict items, empty string) → `()` / skipped, never raises.

### F2. Agent field-gating

- `news` **not** in `fields` → `MarketData.news == {}` and `fetch_news` not consulted (the existing
  OHLCV-only and fundamentals tests must stay green untouched — confirm no re-pin).
- `news` in `fields` with a `FakeDataSource(news=...)` → `MarketData.news` carries the fixture
  headlines; quality clean.
- `FakeDataSource(fail_news=True)` with `news` requested → `MarketData.news == {}`, quality notes
  include `"news_degraded"`, `used_fallback is True`, and the **OHLCV path is unaffected** (bars still
  validated). Mirror the S34 `fundamentals_degraded` test.

### F3. Regression

- `FakeDataSource`/`StooqDataSource` with no news fixture and no `news` field requested →
  `MarketData.news == {}` everywhere; full analyst + pipeline suites unchanged (the analyst does
  **not** request `news` yet — that wiring lands in the scoring sprint). Run the whole suite.

## Steps

1. Branch `sprint-36-provider-news-feed` off `main`.
2. **A** settings → **B** news source (+ F1) → **C** port + fakes → **D** composite → **E** agent.
3. `make ci`. Add **F2/F3**; full-suite regression green at the coverage floor (100.00).
4. `wc -l agents/provider/*.py` — every file < 200 (warn 150).
5. Push; hand back.

## Acceptance criteria

- `fetch_news` returns per-ticker tuples of recent headline strings, capped at `max_news_per_ticker`,
  over the trailing `finnhub_news_lookback_days` window; skips tickers with no usable headline; the
  pure parser never raises.
- `get_market_data` populates `MarketData.news` only when `"news"` is in `fields`; a news-fetch fault
  degrades to `{}` + `"news_degraded"` note + `used_fallback`, leaving the OHLCV (and fundamentals)
  paths intact.
- **No contract change** (CONTRACT version, `owns_graph`, `external_io` untouched); **no new
  dependency** (stdlib `urllib`/`json` only).
- Existing callers (OHLCV-only, fundamentals) see `MarketData.news == {}` → **no test re-pin**.
- `make ci` green at/above floor 100.00; import-linter kept; every touched/new module < 200L.

## Out of scope (the rest of phase P12 — see ADR-0002)

This feed is **step 1 of P12 (sentiment, champion–challenger)**; the architecture is settled in
`docs/decisions/0002-sentiment-champion-challenger.md`. Later sprints, not this one:

- **Analyst lexicon pillar (champion)** — a deterministic Loughran–McDonald `score_sentiment(headlines)`
  becomes the *binding* third pillar (`sentiment_weight` 0.20), folded into the renormalised blend
  `(w_t·tech + w_f·fund + w_s·sent)/Σ present`, setting `Recommendation.sentiment_score`; the analyst
  then requests the `"news"` field and writes each per-ticker reading to the graph for alignment.
- **Provider-sentiment challenger** (Finnhub `/news-sentiment`, advisory/shadow) and the
  **forecaster/FinBERT agent** (advisory, heavy dep isolated behind the agent boundary) — neither
  gates; both write readings aligned to the lexicon's.
- **Relationship/scorecard harness** — compares the three scorers on forward returns and promotes via
  the P10 registry gate. (The lexicon-vs-FinBERT question is **resolved** by ADR-0002: lexicon is the
  binding champion, FinBERT an advisory challenger — not an either/or.)
- Persisting news to the graph; relative strength; signal-diversity selection; PM/scanner/reporter
  gaps. Any change outside the provider package + its tests.

## Handback report (paste into PR / reply)

- Confirm no contract change (provider CONTRACT version, `owns_graph`, `external_io` all untouched)
  and that no new dependency was added.
- Where `fetch_news` lives (extended `FinnhubDataSource` vs. a new file/class) and why.
- How `_parse_news` handles the cap, the trailing window, and malformed/missing headlines.
- Confirmation that OHLCV-only and fundamentals callers re-used their pinned values (only the new
  news-bearing tests were pinned fresh).
- Final line counts for every touched/new provider module; new coverage % and floor; total test
  count.

The planning agent reviews, merges to `main`, and plans P12's next sprint — the analyst lexicon
sentiment pillar (the binding champion) — per ADR-0002.
