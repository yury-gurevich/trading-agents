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
| provider | ✅ v1.1 (LOCKED) | 16 / 62 | 🟨 partial — **16 of 62 clauses proven** after the S156 citation check; S187 added PARAM rows only, so counters did not move; 24 have a gray row and 22 have no row at all (S157 warn-only backlog) · S169-sweep demoted `PROV-OUT-04` |
| scanner | ✅ v1.1 (LOCKED) | 18 / 41 | 🟨 partial — **18 of 41 clauses proven**: the S156 citation check plus `SCAN-OUT-06`/`SCAN-OUT-07` added and proven green by S183 (two clauses, three rows — two rows cite `SCAN-OUT-06`); 10 have a gray row and 13 have no row at all (S157 warn-only backlog) |
| analyst | ✅ v1.2 (LOCKED) | 24 / 47 | 🟨 partial — **24 of 47 clauses proven** after S186 adds and proves `ANLZ-OBS-04`; 10 have a gray row and 12 have no row at all (S157 warn-only backlog) · S152 declared 3 new clauses (43→46) · S169-sweep demoted `ANLZ-OBS-01` |
| forecaster | ✅ v1 (LOCKED) | 16 / 45 | 🟨 partial — **16 of 45 clauses proven** after the S156 citation check; 29 have a gray row |
| portfolio_manager | ✅ v1 (LOCKED) | 28 / 47 | 🟨 partial — **28 of 47 clauses proven** after S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows; 12 law clauses still have no row (S157 warn-only backlog) |
| deliberator | ✅ v1.1 (LOCKED) | 9 / 51 | 🟨 partial — **9 of 51 clauses proven** after S189 adds stop-reason audit evidence, stopped-completion failure, and the empty-turn prohibition; S167 proves queryable fail-open causes (`DLIB-OBS-03`) |
| execution | ✅ v1.3 (LOCKED) | 33 / 60 | 🟨 partial — **33 of 60 clauses proven** after S185 declared and proved deliberation posture (`EXEC-OUT-09`, `EXEC-NEV-06`, `EXEC-OBS-04`); S187 added a PARAM row only, so counters did not move; 12 have a gray row and 13 have no row at all (S157 warn-only backlog) · S152 declared 8 new clauses (49→57); `chore-exec-fail-03-coverage` proved EXEC-FAIL-03 · S169-sweep demoted `EXEC-OBS-01` and `EXEC-OBS-02` |
| monitor | ✅ v1 (LOCKED) | 20 / 46 | 🟨 partial — **20 of 46 clauses proven** after the S156 citation check; 19 have a gray row and 7 have no row at all (S157 warn-only backlog) |
| reporter | ✅ v1 (LOCKED) | 20 / 39 | 🟨 partial — **20 of 39 clauses proven** after the S156 citation check; 18 have a gray row and 1 have no row at all (S157 warn-only backlog) |
| researcher | ✅ v1 (LOCKED) | 19 / 43 | 🟨 partial — **19 of 43 clauses proven** after the S156 citation check; 24 have a gray row |
| curator | ✅ v1 (LOCKED) | 22 / 47 | 🟨 partial — **22 of 47 clauses proven** after the S156 citation check; 25 have a gray row |
| operator | ✅ v1 (LOCKED) | 15 / 50 | 🟨 partial — **15 of 50 clauses proven** after the S156 citation check; 35 have a gray row |
| supervisor | ✅ v1 (LOCKED) | 21 / 48 | 🟨 partial — **21 of 48 clauses proven** after S179 proves append-only `FaultResolution` retirement (`SUP-OBS-03`); 27 have a gray row |
| master | ✅ v1.2 (LOCKED) | 15 / 44 | 🟨 partial — **15 of 44 clauses proven** after S188 adds and proves credential-test handover guards; 8 have a gray row and 21 have no row at all (S157 warn-only backlog) · RSA signing + Key Vault + integration clauses deferred (S73/S74) |

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
