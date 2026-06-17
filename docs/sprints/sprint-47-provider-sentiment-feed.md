<!-- Agent: planning | Role: sprint handover -->
# Sprint 47 — Provider serves vendor sentiment into MarketData.sentiment (P12)

**Status:** shipped · **Branch:** `sprint-47-provider-sentiment-feed` · **Build phase:** P12 (provider-sentiment challenger) · **Effort: M–L**

## Goal

Flow the Alpha Vantage vendor sentiment (source + probe shipped previously) through the provider's
`DataSource` boundary into a new `MarketData.sentiment: dict[Ticker, float]` field — the S36-news twin,
one boundary over. This makes the provider-sentiment challenger's number available to the analyst (the
shadow-reading consumption is the next slice). Source: ADR-0002 (Alpha Vantage replaces dead Finnhub
`/news-sentiment`).

## What shipped

- **`DataSource` Protocol** gains `fetch_sentiment(tickers) -> dict[str, float]` (windowless — sentiment
  is "latest"). All implementers stub it: `StooqDataSource`, `FMPDataSource`, `TiingoDataSource`,
  `FinnhubDataSource` → `{}`; `FakeDataSource` gains a `sentiment` fixture + `fail_sentiment`;
  `AlphaVantageSentimentSource` is now a full `DataSource` (sentiment real, OHLCV/fundamentals/news/
  regime stubbed — like FMP is OHLCV-only).
- **`CompositeDataSource`** gains a third `sentiment_source` and routes `fetch_sentiment` to it;
  `market_source_from_settings` wires Alpha Vantage as that source.
- **Provider agent** field-gates `"sentiment"` in `get_market_data` with its own `fault_boundary` →
  `{}` + a `"sentiment_degraded"` quality note + `used_fallback` on fault (the news/fundamentals shape).
- **Contract:** `MarketData.sentiment` (default `{}`), `DataRequest.fields` documents `sentiment`,
  `external_io += "alphavantage"` (single-writer holds), version `0.1.0 → 0.2.0`.
- **Refactor:** `StooqDataSource` (retired) extracted to `agents/provider/stooq.py` to keep
  `sources.py` < 200L; its tests moved to `test_stooq.py`.

## Acceptance (met)

- `get_market_data` populates `MarketData.sentiment` only when `"sentiment"` ∈ `fields`; a sentiment
  fault degrades to `{}` + `"sentiment_degraded"` note, leaving OHLCV/fundamentals/news intact.
- No new dependency (stdlib only); single-writer-per-label + exclusive-external-io meta-tests hold.
- `make ci` green at floor 100.00 (651 passed); every module < 200L.

## Out of scope (next slice)

The **analyst** consumption: request the `"sentiment"` field, and write a 2nd `SentimentReading`
(`scorer="provider"`, aligned to the lexicon) — **shadow, never gates** (the S46 node already supports
it). Then the **forecaster/FinBERT** scorer and the **scorecard harness** (per ADR-0002).
