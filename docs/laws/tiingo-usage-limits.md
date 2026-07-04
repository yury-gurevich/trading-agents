# Tiingo Usage Limits — Mandatory Live-Use Preflight

Before any live script, sprint check, probe, or backfill uses Tiingo, read this
note and plan the request budget first. The in-tree `TiingoDataSource` currently
uses one HTTP request per ticker for EOD history.

Current published free-tier limits, verified on 2026-07-04:

| Limit | Free tier |
| --- | --- |
| Requests per hour | 50 |
| Requests per day | 1,000 |
| Unique symbols per month | 500 |
| Monthly bandwidth | 1 GB |

Reset cadence from Tiingo documentation:

| Budget | Reset |
| --- | --- |
| Hourly requests | Every hour |
| Daily requests | Midnight EST |
| Monthly bandwidth | First of the month at midnight EST |

Operational rule:

- Do not run a >50-symbol Tiingo export as a single uninterrupted free-tier job.
- Use the committed `scripts/export_tiingo_bars.py` exporter for return-model
  backfills and sprint checks. It writes `date,ticker,close,volume`, skips
  tickers already present in the CSV, and defaults to a 72-second pace
  (50 requests/hour).
- Stop on HTTP 429 responses and resume after the hourly reset. A 429 is a
  budget signal, not a transient error to retry in a tight loop.
- Bounded retry/backoff is for transient 5xx/timeout failures only. The exporter
  defaults to two retries with linear backoff before skipping that ticker.
- For S&P share classes, prefer Tiingo's dash symbology when needed
  (`BRK-B`, not `BRK.B`).
- For broad, repeated OHLCV backfills, prefer a future provider-selectable
  exporter using `AlpacaDataSource`: Alpaca is the primary OHLCV path and
  batches many symbols per request. Tiingo is the cheap fallback and raw-history
  lineage source. Sprint evidence that explicitly requires DL-37 Tiingo lineage
  must still use Tiingo and say so.

Sources:

- https://www.tiingo.com/pricing
- https://www.tiingo.com/documentation/
- https://www.tiingo.com/products/end-of-day-stock-price-data
