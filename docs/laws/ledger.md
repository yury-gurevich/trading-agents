# The landscape — gray → green ledger

The single board for "do we KNOW it works." A row is **green** only when every non-deprecated law in
that scope has ≥ 1 passing functional test citing its ID, and its dependencies are green
(conventions §3). Everything starts **gray** (written in hope) and earns green (proven).

Legend: ⬜ gray (unproven) · 🟩 green (proven) · 🟨 partial · ⛔ blocked by a gray dependency.

## Layer 0 — Dependencies (must go green first)

| Component | Clauses | Status |
| --- | --- | --- |
| DEP-CONFIG | 2 | ⬜ |
| DEP-CLOCK | 1 | ⬜ |
| DEP-NEO4J | 3 | 🟨 **2/3 real** — 01 reachable + 02 write/read proven on Aura (`02812797`); 03 append-only/uniqueness pending |
| DEP-BUS | 3 | ⬜ |
| DEP-FEED | 3 | ⛔ **live Stooq RED** (anti-bot proof-of-work blocks the HTTP client → 404); **Postgres price_cache fallback 🟩** (1285 AAPL bars to 2026-05) |
| DEP-BROKER | 2 | ⬜ |
| DEP-LLM | 2 | ⬜ |
| DEP-TELE | 2 | ⬜ |

> **First real probe run (2026-06-16).** Through the functional channels: Neo4j Aura round-trips for
> real; the provider's `StooqDataSource` gets a 404 (Stooq now serves a JS proof-of-work interstitial,
> not CSV) — so the keyless live OHLCV feed is **non-functional programmatically**; the Postgres
> historical store serves OHLCV as the fallback. This is the gray→green machine catching a load-bearing
> break that the `FakeDataSource` unit tests never could.

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
