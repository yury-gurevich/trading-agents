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
- Use resumable scratch scripts that append successful tickers and skip already
  exported symbols.
- Stop on sustained HTTP 429 responses and resume after the hourly reset.
- For S&P share classes, prefer Tiingo's dash symbology when needed
  (`BRK-B`, not `BRK.B`).

Sources:

- https://www.tiingo.com/pricing
- https://www.tiingo.com/documentation/
- https://www.tiingo.com/products/end-of-day-stock-price-data
