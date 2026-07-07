# The landscape — gray → green ledger

The single board for "do we KNOW it works." A row is **green** only when every non-deprecated law in
that scope has ≥ 1 passing functional test citing its ID, and its dependencies are green
(conventions §3). Everything starts **gray** (written in hope) and earns green (proven).

Legend: ⬜ gray (unproven) · 🟩 green (proven) · 🟨 partial · ⛔ blocked by a gray dependency.

## Layer 0 — Dependencies (must go green first)

Re-run the live harness any time: **`uv run --extra runtime python -m probes`**
(`probes/`, real systems, functional channels). Latest Postgres dependency proof (2026-07-07, S117):
`DEP-CONFIG-01` green with `POSTGRES_DSN`; `DEP-POSTGRES-01` green with live Neon `SELECT 1`;
Alembic head applied before the fleet slice; durable rows were verified from a separate raw connection
and torn down to zero. Historical Neo4j rows remain valid evidence for the pre-S117/S118 spine only.

| Component | Clauses | Status |
| --- | --- | --- |
| DEP-CONFIG | 2 | 🟩 01 real (`POSTGRES_DSN` + feed/LLM creds present) |
| DEP-CLOCK | 1 | 🟩 01 real (UTC instant) |
| DEP-POSTGRES | 3 | 🟩 **3/3 real** — `01` live Neon connect + `SELECT 1`; `02` Alembic `upgrade head` wired as the pre-start deploy step; `03` S116 parity + S117 served-slice durability/teardown prove append-only props, edge identity, traversal parity, and no destructive default ops |
| DEP-BUS | 3 | 🟩 **Service Bus live for fleet serve path** — S100 proved the receiver/claim-check parity on disposable topics; S102 proved five served-agent request/reply round-trips over `trading-agents-bus` from separate processes into five Container Apps. |
| DEP-FEED | 3 | 🟩 **OHLCV live**: **Tiingo probed green** (runtime default, S44 — 9 AAPL EOD bars via `TiingoDataSource`); **FMP** 🟩 (failover/validation, 1255 bars); **Finnhub fundamentals 🟩** (11 AAPL metrics). Stooq retired (anti-bot). Postgres raw fallback retired 2026-06-19 (Tiingo + Alpaca cover the need). |
| DEP-BROKER | 2 | 🟩 **2/2 real** — `probe_broker` against **live Alpaca paper** (`AlpacaBroker`, S45): **01** submit returned a real order (`7327477f-b5a`, pending); **02** same `client_order_id` replayed to one order (422→fetch); cleanup canceled it → account flat. `broker_from_settings` default (Alpaca when keyed, else PaperBroker for the unit gate). |
| DEP-LLM | 2 | ⬜ key present (Anthropic); live ping gated for cost |
| DEP-TELE | 2 | ⬜ Azure Monitor live (`AZURE_OBSERVABILITY_ENABLED=true`); Azure Managed Prometheus remote-write URL present; `prometheus-client` → Azure path not yet formally proven in live harness; Event Hubs not provisioned (ADR-0003) |

> **The harness already paid for itself (2026-06-16).** Through the functional channels it proved Neo4j
> Aura green (incl. uniqueness) and **caught a load-bearing break**: the provider's `StooqDataSource`
> gets a 404 because Stooq now serves a JS proof-of-work interstitial, not CSV — the keyless live OHLCV
> feed is non-functional programmatically. After S117, PostgreSQL is the graph system of record; Tiingo
> and Alpaca cover the raw-market-data need. No `FakeDataSource` unit test could have surfaced this.

## Layer 1 — Agents

| Agent | Laws authored? | Clauses green / total | Status |
| --- | --- | --- | --- |
| provider | ✅ v1 (LOCKED) | 23 / 43 | 🟨 partial — 23 clauses green (S69 citation pass); 20 gap-tests remain ⬜ (written in later sprints); template now locked for copying to other agents |
| scanner | ✅ v1 (LOCKED) | 18 / 39 | 🟨 partial — 18 clauses green (S70 citation pass); 21 gap-tests remain ⬜ |
| analyst | ✅ v1 (LOCKED) | 24 / 43 | 🟨 partial — 24 clauses green (S70 citation pass); 19 gap-tests remain ⬜ |
| forecaster | ✅ v1 (LOCKED) | 16 / 46 | 🟨 partial — 16 clauses green (S99 served-entrypoint pass); 30 gap-tests remain ⬜ |
| portfolio_manager | ✅ v1 (LOCKED) | 23 / 43 | 🟨 partial — 23 clauses green (S70 citation pass); 20 gap-tests remain ⬜ |
| execution | ✅ v1 (LOCKED) | 30 / 49 | 🟨 partial — 30 clauses green (S70 citation pass); 19 gap-tests remain ⬜ |
| monitor | ✅ v1 (LOCKED) | 19 / 40 | 🟨 partial — 19 clauses green (S71 citation pass); 21 gap-tests remain ⬜ |
| reporter | ✅ v1 (LOCKED) | 17 / 40 | 🟨 partial — 17 clauses green (S71 citation pass); 23 gap-tests remain ⬜ |
| researcher | ✅ v1 (LOCKED) | 19 / 44 | 🟨 partial — 19 clauses green (S99 served-entrypoint pass); 25 gap-tests remain ⬜ |
| curator | ✅ v1 (LOCKED) | 22 / 48 | 🟨 partial — 22 clauses green (S99 served-entrypoint pass); 26 gap-tests remain ⬜ |
| operator | ✅ v1 (LOCKED) | 14 / 51 | 🟨 partial — 14 clauses green (S71 citation pass); 37 gap-tests remain ⬜ |
| supervisor | ✅ v1 (LOCKED) | 21 / 49 | 🟨 partial — 21 clauses green (S71 citation pass); 28 gap-tests remain ⬜ |
| master | ✅ v1 (LOCKED) | 10 / 18 | 🟨 partial — 10 clauses green (S73); 8 deferred (RSA signing + Key Vault + integration) |

## Layer 2 — Choreography

Every edge in [`flow.md`](flow.md) type-aligned and proven on a real run. 🟩 **PROVEN LIVE
2026-07-07 in S102**: 13 branch-tagged Container Apps (`:s102`) on the Postgres spine processed one
manual `RunRequest` (`s102-dist-20260707T1530Z`) by graph-pull across containers:
`RunRequest -> MarketData -> ScanRun -> AnalystRun -> PMRun -> ExecutionRun -> MonitorRun -> Snapshot`.
The run returned `OBSERVATORY  OK - all invariants hold` and
`ACCEPTANCE  PASS - every stage did its job within its boundaries`; five served control-plane agents
also round-tripped over Azure Service Bus.

## Layer 3 — Acceptance

One full paper-trading day on real S&P 500 data, persisted, with each agent's job + boundaries
asserted. 🟩 **at the full S&P-500** ("the system works") — proven live 2026-06-26 after the
[DRIFT-014](drift-register.md) per-ticker-quality fix.

- **Gate (DL-28, 0.35.00):** `scripts/accept.py` / `accept_run` — every per-stage invariant + cross-stage
  **conservation** (no agent fabricates or overruns its input). Deterministic CI guard green.
- **PROVEN LIVE on a full S&P-100 → Aura run (2026-06-25, 0.35.02):** all 99 names × 41 real bars,
  provider→reporter, **5 positions opened**, `OBSERVATORY OK` + **`ACCEPTANCE PASS - every stage did its
  job within its boundaries`**. The road there fixed three live-only bugs the in-memory suite hid:
  [DRIFT-011](drift-register.md) (run_id keying), [DRIFT-012](drift-register.md) (optional-field over-taint
  + sigma).
- **Caveat (not blocking):** [DRIFT-013](drift-register.md) — the 5 names are correlated and PM-NEV-06 was
  silently inactive (empty `sectors` from a Finnhub rate-limit). Trades cleanly, not yet wisely; tracked.
- **S&P-500 scale (2026-06-25):** committed `universe_sp500.txt` (503 names, authoritative); the run
  completed — **Alpaca pulled 503/503 OHLCV, the data layer scales** — but `ACCEPTANCE FAIL`:
  [DRIFT-014](drift-register.md), per-batch quality (one >8σ name taints all 503 → analyst rejects the
  clean survivors). **Fixed (0.37.01):** the outlier is now attributed to its own ticker and *excluded*
  (`anomalous_tickers`), not tainting the batch. **🟩 PROVEN LIVE (2026-06-26):** a full S&P-500 → Aura
  acceptance run (OHLCV-only, 9.4s) returned `ACCEPTANCE PASS` — provider flagged `anomalous SMCI`, batch
  stayed `quality ok returned=502/503`, **2 positions opened**. The OHLCV-only fast mode (9.4s vs ~33 min)
  is demonstrated; a CLI/env toggle for it is a small follow-up.
