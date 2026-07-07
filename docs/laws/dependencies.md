# Layer-0 — Dependency charter (the green bill of health)

Agents are independent of **each other**, but they stand on shared **infrastructure**. Each component
below must earn a **green bill of health** (its `DEP-*` clauses proven) **before** any agent that
relies on it can be counted green (conventions §3). A red dependency forces the dependent agent's
failure law (e.g. fail-loud / degrade), never fabrication.

Health is proven by a **dependency probe** — a check that the component is reachable and behaves to
contract — runnable in isolation and as the pre-flight of any real run.

## DEP-POSTGRES — system-of-record graph spine

- `DEP-POSTGRES-01` — reachable with the configured `POSTGRES_DSN` and answers `SELECT 1`.
- `DEP-POSTGRES-02` — schema is Alembic-managed and upgraded to head before fleet startup.
- `DEP-POSTGRES-03` — graph-store parity holds: append-only props, edge identity,
  depth/filter/dedup traversal, and no destructive GraphStore operations.

## DEP-BUS — message bus (in-process now; Azure Service Bus later, ADR-0005; transitional CeleryBus retires at P14)

- `DEP-BUS-01` — a request reaches a bound handler and the response returns.
- `DEP-BUS-02` — a handler fault becomes a typed error envelope, not a hang/crash.
- `DEP-BUS-03` — (distributed) delivery is acknowledged; failures dead-letter, not vanish.

## DEP-FEED — external market-data feed(s)

Feed strategy is **ADR-0006** plus DL-16/DL-37: **Alpaca** is the primary runtime/batch OHLCV source
because it fetches many symbols per request; **Tiingo** is the cheap fallback and explicit raw-history
lineage source when a sprint requires DL-37 Tiingo-sourced evidence (free tier: 500 unique
symbols/month, 50 requests/hour); **FMP** (free, ~87 symbols) is a validation sub-universe; **Finnhub**
(free) serves fundamentals + news. No anti-bot scraping (Stooq retired). Postgres `price_cache` was
the raw-OHLCV backtest fallback — **retired 2026-06-19** (Tiingo + Alpaca cover the need;
repo-hygiene.md pass 3). Paid feeds deferred to Phase D.

- `DEP-FEED-01` — the price feed is reachable and returns parseable data for a known symbol.
- `DEP-FEED-02` — the keyed feed (Finnhub fundamentals/news; Alpha Vantage vendor sentiment)
  authenticates and respects rate limits.
- `DEP-FEED-03` — an unreachable/garbled feed is detectable as such (so the provider can degrade
  honestly, not fabricate).

## DEP-BROKER — broker boundary (paper now; real later)

Broker is **Alpaca** (ADR-0006): paper trading now (`ALPACA_ENDPOINT=paper-api…`) → live later; the
same Alpaca credential also backs DEP-FEED failover (one vendor, data + execution).

- `DEP-BROKER-01` — accepts an order and returns a fill record.
- `DEP-BROKER-02` — is idempotent: the same order key submitted twice fills once.

## DEP-LLM — language-model provider (operator / forecaster)

- `DEP-LLM-01` — authenticates and returns a well-formed response within the timeout.
- `DEP-LLM-02` — a failure degrades to a typed error, never a fabricated decision.

## DEP-CLOCK — time source

- `DEP-CLOCK-01` — supplies a UTC instant; used for staleness, time-exits, and provenance stamps.

## DEP-CONFIG — config & secrets loading

- `DEP-CONFIG-01` — required keys for the active stage are present; missing → loud failure at start.
- `DEP-CONFIG-02` — secrets are never emitted in logs, responses, or errors.

## DEP-TELE — telemetry / log plane (ADR-0003) & metrics (P9)

- `DEP-TELE-01` — log events reach the plane (or fall back) without blocking the trading path.
- `DEP-TELE-02` — metrics register and scrape.

## Probe sequencing

A real run's pre-flight runs the probes for the dependencies its flow needs, in this order, and
**stops loud** on the first red: `DEP-CONFIG → DEP-CLOCK → DEP-POSTGRES → DEP-BUS → DEP-FEED →
DEP-BROKER → (DEP-LLM) → DEP-TELE`. Green pre-flight is the precondition for trusting any agent-level
result. Neo4j is an out-of-bounds workbench, not a Layer-0 runtime dependency.

**The probes are real and runnable** — the `probes/` package hits the actual systems through the
provider's functional channels (no mocks), reading creds from `.env` (v1 `.env` fallback):

```bash
uv run --extra runtime python -m probes   # prints the bill of health; exits non-zero on RED
```

It is **not** part of the unit gate (`probes/` is outside `testpaths` and coverage `source`) — it is an
on-demand pre-flight against live infrastructure. Status lives in [`ledger.md`](ledger.md).
