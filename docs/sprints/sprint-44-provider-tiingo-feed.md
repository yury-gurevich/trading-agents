<!-- Agent: planning | Role: sprint handover -->
# Sprint 44 — Provider Tiingo OHLCV feed (full-S&P-500 live default)

**Status:** MERGED — `25dda634` on `main` (feat(provider): Tiingo live OHLCV feed as the full-S&P-500 default (S4) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-44-provider-tiingo-feed` · **Build phase:** provider infra (DRIFT-009 closeout · ADR-0006) · **Effort: M**

## Goal

Make the provider's live OHLCV feed **real for the full S&P 500** by adding a `TiingoDataSource` and
making it the runtime default. Today the default source is `StooqDataSource`, which is
**anti-bot-blocked and broken** (DRIFT-009); the interim `FMPDataSource` works but covers only a
curated **~87-symbol subset** (PG, HD return `402`). **Tiingo's free tier covers the whole index**
(500 unique symbols/month, real-time IEX, 30+ yrs history — ADR-0006). This sprint builds the Tiingo
source as the **structural twin of `FMPDataSource`** (read `agents/provider/fmp.py` first), routes
OHLCV to it in `market_source_from_settings`, and re-points the runtime default in
`orchestration/bindings.py` off broken Stooq.

**No contract change.** `OHLCVBar` and the `DataSource` Protocol are unchanged — this is a new adapter
behind the existing boundary plus a one-line default swap.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails); **`docs/decisions/0006-market-data-feed-strategy.md`**
  (the decision this implements); `docs/laws/drift-register.md` DRIFT-009 (the gap this closes).
- **Shipped code you mirror / extend (read it):**
  - **`agents/provider/fmp.py`** — `FMPDataSource`. Your `TiingoDataSource` is this class with a
    different endpoint + date parse. Same shape: `fetch_ohlcv` loops tickers → `_download` →
    `_parse_eod`; `fetch_regime_inputs`→`RegimeInputs(as_of, vix=None)`; `fetch_fundamentals`→`{}`;
    `fetch_news`→`{}`; pure `_parse_eod`/`_bar` that **never raise** and skip out-of-window /
    malformed / non-positive rows; `_download` is `# pragma: no cover`.
  - **`agents/provider/tests/test_fmp.py`** — your `test_tiingo.py` mirrors it (the `MethodType`
    offline-stub pattern for `_download`). **You also edit this file**: the existing
    `test_market_source_from_settings_routes_ohlcv_to_fmp` now asserts the price source is
    `TiingoDataSource` (rename/retarget it — see Part E).
  - **`agents/provider/composite.py`** — `market_source_from_settings` currently builds
    `price_source=FMPDataSource(...)`. Change it to `TiingoDataSource(...)`; the Finnhub
    fundamentals/news wiring stays. `CompositeDataSource` itself is unchanged.
  - **`agents/provider/settings.py`** — FMP settings live here (lines ~97–106). Add the three
    `tiingo_*` fields beside them (Part A). File is at 126L — keep < 200L.
  - **`agents/provider/sources.py`** — the `DataSource` Protocol (no change; `TiingoDataSource`
    structurally satisfies it). Note how `StooqDataSource._download` uses `urllib.request.urlopen`
    with a hardcoded HTTPS URL + `noqa: S310` — copy that shape.
  - **`orchestration/bindings.py`** — line ~21 imports `StooqDataSource`; line ~50
    `source=source or StooqDataSource()`. This is the **runtime default re-point** (Part D).
  - **Do NOT delete `agents/provider/fmp.py`** — FMP is retained as the validation sub-universe and a
    future failover (ADR-0006). It is only demoted from the default.

### The Tiingo call (port this shape)

Tiingo daily EOD: `GET https://api.tiingo.com/tiingo/daily/{ticker}/prices` with query params
`startDate`, `endDate` (ISO `YYYY-MM-DD`), and `token`. Returns a JSON **array** of daily objects:

```json
[{"date":"2026-01-10T00:00:00.000Z","open":100.0,"high":105.0,"low":99.0,
  "close":104.0,"volume":1000000,"adjClose":104.0, "...":"divCash/splitFactor/adj* ignored"}]
```

Two Tiingo specifics that differ from FMP — get them right:

1. **`date` is an ISO _datetime_ with a `Z`** (`"2026-01-10T00:00:00.000Z"`), not a plain date.
   `date.fromisoformat(...)` rejects that — slice first: `date.fromisoformat(str(item["date"])[:10])`.
2. **Use the RAW fields** `open/high/low/close/volume` (not `adj*`) — consistent with `FMPDataSource`
   and what the analyst was tuned on. (Adjusted fields exist if we later want split-adjustment; out of
   scope — note it in the handback, don't switch.)

Auth: put the key in the **`token` query param** (mirrors FMP's `_download` exactly — plain
`urllib.request.urlopen`, no `Request` object needed). An unknown ticker / error returns a non-array
or `[]` → `_parse_eod` yields `()` via its non-list guard (same as FMP).

## Part A — Settings

`agents/provider/settings.py` — add to `ProviderSettings`, beside the FMP block:

```python
# Tiingo — primary full-universe live OHLCV feed (ADR-0006).
tiingo_base_url: str = Field(default="https://api.tiingo.com")
tiingo_api_key: str = Field(default="", repr=False)
tiingo_timeout: int = tunable(
    15,
    why="Bound the Tiingo EOD HTTPS call so a slow feed cannot hang the run.",
    ge=1,
    le=60,
    unit="seconds",
)
```

`tiingo_api_key` reads `PROVIDER_TIINGO_API_KEY` (env_prefix). Note: `.env`/`.env.example` carry the
key as `TIINGO_API_KEY`; the coding agent does **not** edit `.env`. If the prefix mismatch matters for
the live run, flag it in the handback (the planner reconciles env naming) — do not change `env_prefix`.

## Part B — Tiingo source

New `agents/provider/tiingo.py` — ≤ 130L, the structural twin of `fmp.py`:

```python
"""Tiingo daily-EOD source over the provider DataSource boundary.

Agent: provider
Role: fetch daily OHLCV bars from Tiingo's tiingo/daily prices endpoint
(the primary full-universe live OHLCV feed — ADR-0006, DRIFT-009).
External I/O: optional HTTPS calls to api.tiingo.com.
"""
```

- `_PRICES_PATH = "/tiingo/daily/{ticker}/prices"` (format per-ticker, lowercased symbol).
- `TiingoDataSource(*, api_key, base_url, timeout)` — same constructor as `FMPDataSource`.
- `fetch_ohlcv` / `fetch_regime_inputs` / `fetch_fundamentals` / `fetch_news` — identical to
  `fmp.py` (OHLCV only; the other three return empty defaults).
- `_download(ticker, window)` — `# pragma: no cover`; `urlencode({"startDate": window.start.isoformat(),
  "endDate": window.end.isoformat(), "token": self._api_key})`; `urllib.request.urlopen(f"{base}{path}?{query}")`
  with `noqa: S310`.
- Pure `_parse_eod(ticker, raw_json, window)` and `_bar(ticker, item, window)` — copy `fmp.py` exactly
  **except** the date parse: `date.fromisoformat(str(item["date"])[:10])`. Keep the same guards:
  non-list payload → `()`; `KeyError/TypeError/ValueError` → skip row; out-of-window → skip;
  `min(o,h,l,c) <= 0 or volume < 0` → skip. Never raises out of the parser.

## Part C — Composite re-point

`agents/provider/composite.py::market_source_from_settings` — swap the price source:

```python
from agents.provider.tiingo import TiingoDataSource
# ...
return CompositeDataSource(
    price_source=TiingoDataSource(
        api_key=settings.tiingo_api_key,
        base_url=settings.tiingo_base_url,
        timeout=settings.tiingo_timeout,
    ),
    fundamentals_source=FinnhubDataSource(...),  # unchanged
)
```

Update the function docstring (FMP → Tiingo OHLCV). Leave the FMP import out of this function (FMP is
no longer the default); `fmp.py` stays in the tree for validation/failover.

## Part D — Runtime default re-point

`orchestration/bindings.py` — stop defaulting to broken Stooq:

- Replace the `StooqDataSource` import with `from agents.provider.composite import market_source_from_settings`.
- Build the provider settings **once** and reuse for both the source and the agent:

  ```python
  provider_settings = ProviderSettings(
      max_staleness_days=settings.provider_max_staleness_days
  )
  ProviderAgent(
      bus,
      graph=graph,
      source=source or market_source_from_settings(provider_settings),
      settings=provider_settings,
      sink=sink,
  ).bind()
  ```

The default is only constructed when no `source` is injected; every test/caller that injects a
`FakeDataSource` is unaffected. **Check** for any test that relied on the `StooqDataSource` default
(grep `bind_paper_loop_agents` callers with `source=None`); if one exists, inject a `FakeDataSource`
there instead of standing up a live feed — flag it in the handback.

## Part E — Tests

### E1. `agents/provider/tests/test_tiingo.py` — ≤ 110L

Mirror `test_fmp.py` (the `MethodType` offline-stub of `_download`):

- Parses a normal two-bar array; bars carry the right `bar_date`/`close`/`volume`; **the `Z`-suffixed
  ISO datetime is parsed to the correct `date`** (the key Tiingo-specific assertion).
- Filters out-of-window + malformed + non-positive rows (twin of the FMP filter test).
- Non-array payload (e.g. `{"detail":"Error"}`) → `()`.
- `fetch_fundamentals`/`fetch_news`/`fetch_regime_inputs` return the empty defaults.

### E2. Retarget the composite-routing test

In `test_fmp.py`, the existing `test_market_source_from_settings_routes_ohlcv_to_fmp` now fails (price
source is Tiingo). **Move it** to `test_tiingo.py` as `test_market_source_from_settings_routes_ohlcv_to_tiingo`
asserting `isinstance(composite._price_source, TiingoDataSource)` (and still
`isinstance(composite, CompositeDataSource)`). Remove the stale FMP version.

### E3. Regression

- Full provider suite + `orchestration` binding tests green. Confirm the `bindings.py` change did not
  re-pin any existing test (they inject sources). Run the whole suite.

## Steps

1. Branch `sprint-44-provider-tiingo-feed` off `main`.
2. **A** settings → **B** `tiingo.py` (+ E1) → **C** composite → **D** bindings → **E2/E3**.
3. `make ci`; full-suite regression green at the coverage floor (100.00).
4. `wc -l agents/provider/*.py orchestration/bindings.py` — every file < 200 (warn 150).
5. Push; hand back.

## Acceptance criteria

- `TiingoDataSource.fetch_ohlcv` returns in-window `OHLCVBar`s parsed from Tiingo's daily-prices array,
  correctly parsing the `Z`-suffixed ISO datetime to a `date`; the pure parser never raises and skips
  out-of-window / malformed / non-positive rows.
- `market_source_from_settings` routes **OHLCV → Tiingo**, fundamentals/news → Finnhub (unchanged).
- `bind_paper_loop_agents`' default source is the live composite (Tiingo+Finnhub), **not**
  `StooqDataSource`; injected sources still win.
- **No contract change** (`OHLCVBar`, `DataSource` Protocol untouched); **no new dependency** (stdlib
  `urllib`/`json` only); `fmp.py` retained.
- `make ci` green at/above floor 100.00; import-linter kept; every touched/new module < 200L.

## Out of scope (explicit — flag, don't build)

- **Failover chaining** (Tiingo → FMP → Alpaca on empty/error). A `FailoverDataSource` wrapper is a
  separate sprint; this one makes Tiingo the single live default.
- **`AlpacaDataSource`** and the Alpaca **broker** adapter (paper P/L, "fake purchases") — separate
  later sprint; Alpaca is locked as the broker in ADR-0006 but not built here.
- **Scanner symbol-budget enforcement** (keep the live universe ≤ 500/month for Tiingo free) — a
  scanner-side concern, not this source.
- **Adjusted-price switch** (`adj*` fields) — note availability in the handback; do not change behaviour.
- Editing `.env`/`.env.example`, the probe harness, or any `infra/*` file (external-agent territory).

## Handback report (paste into PR / reply)

- Confirm no contract change and no new dependency; `fmp.py` retained.
- How `_parse_eod`/`_bar` handle the `Z`-suffixed date, the window filter, and malformed/error payloads.
- The `bindings.py` default swap, and whether any caller relied on the `StooqDataSource` default
  (and how you handled it).
- The `PROVIDER_TIINGO_API_KEY` vs `.env`'s `TIINGO_API_KEY` prefix question (for the planner to
  reconcile env naming) and whether you used raw vs adjusted prices.
- Final line counts for every touched/new module; new coverage % and floor; total test count.

The planning agent reviews, merges to `main`, marks **DRIFT-009 CORRECTED** (live default shipped),
updates STATE, and plans the **failover wrapper + `AlpacaDataSource`/broker** follow-ups (ADR-0006).
