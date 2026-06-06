# Provider Agent

**Mission.** Be the single boundary to the outside market world. Turn raw external
feeds (prices, fundamentals, news, macro) into clean, validated, cached market
facts and the current regime — so no other agent ever calls an external data API.

## Owns
- Provider clients (stooq, finnhub, fred, edgar, finbert, S&P 500 listing).
- The price cache and provider snapshots.
- Market-regime classification and the policy inputs every downstream agent reads.
- Honest data-quality accounting (fallbacks, staleness) as a first-class output.

## Boundary — contract: `contracts/provider.py`
- **Consumes:** `get_market_data(DataRequest) -> MarketData`,
  `get_regime(RegimeRequest) -> RegimeContext`.
- **Emits:** `market_data_degraded`.
- **Depends on:** nothing (it is the root of the data graph).

## Data ownership
- **Postgres:** `price_cache`, `provider_snapshots`, `data_quality_log`.
- **Graph:** `MarketSnapshot`, `Regime`, `Ticker`.

## External I/O (exclusive)
- stooq, finnhub, fred, edgar, finbert, S&P 500 listing. **No other agent may
  hold these credentials or call these APIs.**

## MCP surface
- `get_market_data`, `get_regime` (read-only resources).

## Never
- Make a trading decision.
- Be imported by another agent — callers send a request.
- Leak raw provider credentials downstream.
