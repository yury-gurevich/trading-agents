# The landscape — gray → green ledger

The single board for "do we KNOW it works." A row is **green** only when every non-deprecated law in
that scope has ≥ 1 passing functional test citing its ID, and its dependencies are green
(conventions §3). Everything starts **gray** (written in hope) and earns green (proven).

Legend: ⬜ gray (unproven) · 🟩 green (proven) · 🟨 partial · ⛔ blocked by a gray dependency.

## Layer 0 — Dependencies (must go green first)

Re-run the live harness any time: **`uv run --extra runtime --extra probes python -m probes`**
(`probes/`, real systems, functional channels). Latest run (2026-06-16): **12 green · 0 warn · 0 red · 2 skip** — every live dependency green: **Tiingo OHLCV** (runtime default), FMP, Postgres, Finnhub, Neo4j (3/3), and the **live Alpaca paper broker** (submit→idempotent→cancel).

| Component | Clauses | Status |
| --- | --- | --- |
| DEP-CONFIG | 2 | 🟩 01 real (Neo4j + 3 feed/LLM creds present) |
| DEP-CLOCK | 1 | 🟩 01 real (UTC instant) |
| DEP-NEO4J | 3 | 🟩 **3/3 real** — reachable + write/read + **uniqueness enforced** on Aura (`02812797`) |
| DEP-BUS | 3 | ⬜ in-process; covered by the unit gate (not in the live harness) |
| DEP-FEED | 3 | 🟩 **OHLCV live**: **Tiingo probed green** (runtime default, S44 — 9 AAPL EOD bars via `TiingoDataSource`); **FMP** 🟩 (failover/validation, 1255 bars); Postgres raw fallback 🟩 (1285 bars); **Finnhub fundamentals 🟩** (11 AAPL metrics). Stooq retired (dropped from the probe). |
| DEP-BROKER | 2 | 🟩 **2/2 real** — `probe_broker` against **live Alpaca paper** (`AlpacaBroker`, S45): **01** submit returned a real order (`7327477f-b5a`, pending); **02** same `client_order_id` replayed to one order (422→fetch); cleanup canceled it → account flat. `broker_from_settings` default (Alpaca when keyed, else PaperBroker for the unit gate). |
| DEP-LLM | 2 | ⬜ key present (Anthropic); live ping gated for cost |
| DEP-TELE | 2 | ⬜ Prometheus URL present; Event Hubs not provisioned |

> **The harness already paid for itself (2026-06-16).** Through the functional channels it proved Neo4j
> Aura green (incl. uniqueness) and **caught a load-bearing break**: the provider's `StooqDataSource`
> gets a 404 because Stooq now serves a JS proof-of-work interstitial, not CSV — the keyless live OHLCV
> feed is non-functional programmatically. The Postgres raw store covers OHLCV as the fallback. No
> `FakeDataSource` unit test could have surfaced this.

## Layer 1 — Agents

| Agent | Laws authored? | Clauses green / total | Status |
| --- | --- | --- | --- |
| provider | ✅ v0 (draft) | 0 / — | ⬜ template stress-test |
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
