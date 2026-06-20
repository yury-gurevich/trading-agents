# The landscape — gray → green ledger

The single board for "do we KNOW it works." A row is **green** only when every non-deprecated law in
that scope has ≥ 1 passing functional test citing its ID, and its dependencies are green
(conventions §3). Everything starts **gray** (written in hope) and earns green (proven).

Legend: ⬜ gray (unproven) · 🟩 green (proven) · 🟨 partial · ⛔ blocked by a gray dependency.

## Layer 0 — Dependencies (must go green first)

Re-run the live harness any time: **`uv run --extra runtime python -m probes`**
(`probes/`, real systems, functional channels). Latest run (2026-06-17): **13 green · 0 warn · 0 red · 2 skip** — every live dependency green: **Tiingo OHLCV** (default), FMP, Finnhub fundamentals, **Alpha Vantage vendor sentiment** (provider-sentiment challenger), Neo4j (3/3), and the **live Alpaca paper broker** (submit→idempotent→cancel). Postgres probe retired 2026-06-19.

| Component | Clauses | Status |
| --- | --- | --- |
| DEP-CONFIG | 2 | 🟩 01 real (Neo4j + 3 feed/LLM creds present) |
| DEP-CLOCK | 1 | 🟩 01 real (UTC instant) |
| DEP-NEO4J | 3 | 🟩 **3/3 real** — reachable + write/read + **uniqueness enforced**; local Enterprise Docker (`traiding-agents` db, `bolt://localhost:7687`); Aura instance deleted 2026-06-19 |
| DEP-BUS | 3 | ⬜ in-process; covered by the unit gate (not in the live harness) |
| DEP-FEED | 3 | 🟩 **OHLCV live**: **Tiingo probed green** (runtime default, S44 — 9 AAPL EOD bars via `TiingoDataSource`); **FMP** 🟩 (failover/validation, 1255 bars); **Finnhub fundamentals 🟩** (11 AAPL metrics). Stooq retired (anti-bot). Postgres raw fallback retired 2026-06-19 (Tiingo + Alpaca cover the need). |
| DEP-BROKER | 2 | 🟩 **2/2 real** — `probe_broker` against **live Alpaca paper** (`AlpacaBroker`, S45): **01** submit returned a real order (`7327477f-b5a`, pending); **02** same `client_order_id` replayed to one order (422→fetch); cleanup canceled it → account flat. `broker_from_settings` default (Alpaca when keyed, else PaperBroker for the unit gate). |
| DEP-LLM | 2 | ⬜ key present (Anthropic); live ping gated for cost |
| DEP-TELE | 2 | ⬜ Azure Monitor live (`AZURE_OBSERVABILITY_ENABLED=true`); Azure Managed Prometheus remote-write URL present; `prometheus-client` → Azure path not yet formally proven in live harness; Event Hubs not provisioned (ADR-0003) |

> **The harness already paid for itself (2026-06-16).** Through the functional channels it proved Neo4j
> Aura green (incl. uniqueness) and **caught a load-bearing break**: the provider's `StooqDataSource`
> gets a 404 because Stooq now serves a JS proof-of-work interstitial, not CSV — the keyless live OHLCV
> feed is non-functional programmatically. The Postgres raw store covers OHLCV as the fallback. No
> `FakeDataSource` unit test could have surfaced this.

## Layer 1 — Agents

| Agent | Laws authored? | Clauses green / total | Status |
| --- | --- | --- | --- |
| provider | ✅ v1 (LOCKED) | 23 / 43 | 🟨 partial — 23 clauses green (S69 citation pass); 20 gap-tests remain ⬜ (written in later sprints); template now locked for copying to other agents |
| scanner | — | — | ⬜ |
| analyst | — | — | ⬜ |
| forecaster | — | — | ⬜ |
| portfolio_manager | — | — | ⬜ |
| execution | — | — | ⬜ |
| monitor | — | — | ⬜ |
| reporter | — | — | ⬜ |
| researcher | — | — | ⬜ |
| curator | — | — | ⬜ |
| operator | — | — | ⬜ |
| supervisor | — | — | ⬜ |

## Layer 2 — Choreography

Every edge in [`flow.md`](flow.md) type-aligned and proven on a real run. ⬜

## Layer 3 — Acceptance

One full paper-trading day on real S&P 500 data, persisted, with each agent's job + boundaries
asserted. ⬜ — this row turning 🟩 is the definition of "the system works."
