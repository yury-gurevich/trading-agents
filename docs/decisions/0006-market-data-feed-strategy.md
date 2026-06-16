# ADR 0006 — Market-data feed strategy: tiered free feeds behind the DataSource boundary

**Status:** Accepted · **Date:** 2026-06-16 · **Decider:** Yury Gurevich (product owner)

## Context

The provider agent needs **live OHLCV for the full S&P 500** to do real work. The original keyless
feed (Stooq) is **anti-bot-blocked** (PoW interstitial → 404; DRIFT-009); browser-driving it was
rejected (fragile, ToS-gray, and its bulk archive is paywalled anyway). The interim fix, **FMP free**,
was then found to cover only a **curated ~87-symbol subset** — empirically AAPL/TSLA/AMZN/NVDA/MSFT/
JPM/KO/XOM return data but PG and HD return `402 Payment Required`. So FMP free is **not** a
full-universe source.

No single *keyless* source serves the full index live and free. Two free **keyed** tiers do, and both
keys are now **live** (held locally, in `.env`):

- **Tiingo (free).** US & Chinese equities (48,753), 30+ years history, **real-time** (IEX). Free-tier
  API limits: **500 unique symbols/month**, 50 req/hour, 1000 req/day, 1 GB/month; EOD "composite
  prices" + IEX feed; **no** fundamentals or Tiingo News on free; licence *Internal Use Only*. 500
  symbols/month **covers the S&P 500** (≈503 names — right at the cap; manage by rotation/monthly
  reset).
- **Alpaca (free).** Full US market data (IEX feed) **and a broker** (paper + live). One integration
  can serve **both** the provider's OHLCV feed (DEP-FEED) **and** the execution agent's broker
  boundary (DEP-BROKER) — a 2-for-1 architectural fit.

Everything sits behind the provider's **`DataSource`** boundary, so any feed is a drop-in (like the
existing `FMPDataSource`/`FinnhubDataSource`); choosing feeds is a composition decision, not a rewrite.

## Decision

**Use tiered free feeds behind the `DataSource` boundary; do not scrape; defer paid feeds to
production scale.**

- **Primary live OHLCV (full universe): Tiingo (free).** Its 500-symbol/month tier covers the S&P 500
  for EOD + real-time IEX. This is the full-universe live feed.
- **Broker + secondary data: Alpaca (free).** Locked as the **broker** boundary (paper now → live
  later); also a full-US data feed, so it is the **failover** OHLCV source and keeps data + execution
  on one vendor.
- **Supplemental: FMP (free, ~87 symbols)** for a fast liquid-name validation sub-universe; **Finnhub
  (free)** for fundamentals + news (no free candles).
- **Backtest only: Postgres `price_cache`** — raw, full-S&P-500 **historical** OHLCV, frozen
  (RAW DATA ONLY, never v1 derived data; DRIFT-009).
- **No anti-bot scraping** (Stooq retired).
- **Paid feeds are deferred to production (Phase D)** and adopted only if free-tier limits actually
  bind (e.g. intraday cadence, >500 symbols/month, redistribution licence).

## Rationale

- **Full coverage, $0.** Tiingo's free tier reaches the whole index live — the gap FMP free left.
- **One vendor for data + execution.** Alpaca collapses DEP-FEED and DEP-BROKER onto one credential
  and one SLA; the broker is needed regardless, so its data feed is "free" architecturally.
- **Boundary-pure.** The `DataSource` port makes Tiingo/Alpaca drop-ins; swapping or failing over
  between feeds is composition (`composite.market_source_from_settings`), not a code change in agents.
- **Honest degradation.** Multiple keyed feeds give a real failover path; an unreachable feed trips
  the provider's degrade law (DEP-FEED-03), never fabrication.

## Consequences

- **Provider** gains `TiingoDataSource` (and, later, `AlpacaDataSource`) mirroring `FMPDataSource`;
  `market_source_from_settings` re-points OHLCV from FMP → **Tiingo** as the runtime default, with
  Alpaca/FMP as ordered failovers. Settings grow `tiingo_*` (and `alpaca_*`) keys. *(Build step, tied
  to the run-entrypoint — not yet wired.)*
- **`.env.example`** already carries `TIINGO_API_KEY`, `ALPACA_API_KEY/SECRET/ENDPOINT` placeholders
  with acquisition + verify lines.
- **Probe harness** (`probes/feed_ohlcv`) should point its real check at Tiingo (full-universe), with
  Postgres as the documented raw fallback; FMP demoted to the validation sub-universe.
- **DEP-FEED / DEP-BROKER** charter notes Tiingo (primary feed) + Alpaca (broker, secondary feed).
- **Symbol-budget discipline.** Tiingo free = 500 unique symbols/month; the scanner's universe must
  stay within it (or rotate), else failover to Alpaca. A binding cap is a Phase-D paid-feed trigger.

## Alternatives considered

- **FMP free as the universe.** Rejected — ~87 curated symbols (PG/HD return 402); validation only.
- **Browser-scraping Stooq bulk.** Rejected — anti-bot, ToS-gray, bulk is paywalled (401); no prize.
- **Pay for a feed now.** Premature — free tiers cover validation through early production; paid is a
  deliberate Phase-D cost decision, not a default.
- **Alpha Vantage free.** Too rate-limited (≈25 req/day) for a 500-symbol universe.

## Revisit triggers

Adopt a **paid feed** when any free-tier limit binds: intraday/tick cadence required, the live universe
exceeds **500 symbols/month**, request caps (50/hr · 1000/day) throttle the EOD batch, or data
**redistribution** is needed (Tiingo free is *Internal Use Only*). Re-point `market_source_from_settings`;
no agent changes (the `DataSource` boundary holds).
