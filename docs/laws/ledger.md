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
| provider | ✅ v1.3 (LOCKED) | 17 / 62 | 🟨 partial — **17 of 62 clauses proven**; S213 sharpens and proves `PROV-OUT-03` for FMP `^VIX` freshness without adding clauses; S187 added PARAM rows only; S204 gives every clause a row and promotes missing rows to a hard gate; S169-sweep demoted `PROV-OUT-04` |
| scanner | ✅ v1.3 (LOCKED) | 18 / 41 | 🟨 partial — **18 of 41 clauses proven**: S205 rewrites `SCAN-TYP-01` into required fields and closes DRIFT-047 without moving the count; S183 added and proved `SCAN-OUT-06`/`SCAN-OUT-07`; S204 gives every clause a row and promotes missing rows to a hard gate |
| analyst | ✅ v1.6 (LOCKED) | 26 / 49 | 🟨 partial — **26 of 49 clauses proven** after S211 adds and proves `ANLZ-OBS-06`: decision-time favourable-excursion target evidence is measured from prior settled windows, serialized, and missing evidence rejects instead of falling back to a constant target; S205 rewrites `ANLZ-TYP-01` into required fields without moving the count; S198 adds and proves `ANLZ-OBS-05`; S186 adds and proves `ANLZ-OBS-04`; S204 gives every clause a row and promotes missing rows to a hard gate · S152 declared 3 new clauses (43→46) · S169-sweep demoted `ANLZ-OBS-01` |
| forecaster | ✅ v1.3 (LOCKED) | 17 / 45 | 🟨 partial — **17 of 45 clauses proven** after S205 rewrites and proves `FORE-TYP-01`; 28 have a gray row |
| portfolio_manager | ✅ v1 (LOCKED, amended **v1.9**) | 31 / 50 | 🟨 partial — **31 of 50 clauses proven** after S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders the applied weights; S211 adds and proves `PM-OBS-05`: reward-risk now compares measured target evidence against stop risk, varies across measured profiles, and rejects measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows |
| deliberator | ✅ v1.9 (LOCKED) | 23 / 56 | 🟨 partial — **23 of 56 clauses proven** after S222 moves its vendor adapters to `kernel/` and proves `DLIB-SEC-02` with a key-containment sentinel; S214 narrows `vetoed_tickers` to `overturn` verdicts only, routes unreadable judge answers through loud fail-open, and proves `DLIB-OUT-04`; S206 adds and proves `DLIB-NEV-08`: rendered debate-context verdicts name their enforcing check and agent, while descriptive stop-target regime evidence has no verdict; S205 rewrites and proves `DLIB-TYP-01`; S200 adds `DLIB-OBS-07` and promotes `DLIB-IDM-02`; S199 adds `DLIB-OBS-05`/`DLIB-OBS-06`; S172 proves concurrent-order record order and pending-reply handling; S194 adds `DLIB-OBS-04`; S189 added stop-reason audit evidence; S167 proves queryable fail-open causes |
| execution | ✅ v1.8 (LOCKED) | 36 / 62 | 🟨 partial — **36 of 62 clauses proven** after S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 added/proved `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; S204 gives every clause a row and promotes missing rows to a hard gate |
| monitor | ✅ v1.1 (LOCKED) | 21 / 46 | 🟨 partial — **21 of 46 clauses proven** after S205 rewrites and proves `MON-TYP-01`; S204 gives every clause a row and promotes missing rows to a hard gate |
| reporter | ✅ v1.2 (LOCKED) | 25 / 42 | 🟨 partial — **25 of 42 clauses proven** after S226 adds benchmark-relative performance metrics, as-of bounded graph reads, contained performance failure, and backward-compatible `performance_metrics`; S205 rewrites `RPT-TYP-01` into required fields; S204 gives every clause a row and promotes missing rows to a hard gate |
| researcher | ✅ v1.2 (LOCKED) | 20 / 43 | 🟨 partial — **20 of 43 clauses proven** after S205 rewrites and proves `RES-TYP-01`; 23 have a gray row |
| curator | ✅ v1.1 (LOCKED) | 23 / 47 | 🟨 partial — **23 of 47 clauses proven** after S205 rewrites and proves `CUR-TYP-01`; 24 have a gray row |
| operator | ✅ v1.3 (LOCKED) | 18 / 50 | 🟨 partial — **18 of 50 clauses proven** after S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; 32 have a gray row |
| supervisor | ✅ v1.1 (LOCKED) | 22 / 48 | 🟨 partial — **22 of 48 clauses proven** after S205 rewrites and proves `SUP-TYP-01`; S179 proves append-only `FaultResolution` retirement (`SUP-OBS-03`); 26 have a gray row |
| master | ✅ v1.5 (LOCKED) | 18 / 46 | 🟨 partial — **18 of 46 clauses proven** after S217 adds and proves `MST-OUT-04` whole-fleet readiness and `MST-FAIL-05` classification; S205 rewrites and proves `MST-TYP-01`; S188 adds and proves credential-test handover guards; S204 gives every clause a row and promotes missing rows to a hard gate · RSA signing + Key Vault + integration clauses deferred (S73/S74) |

*2026-09-23 — [DL-203](../design-log.md) (work-queue item 33) amended nine of these laws in
their `PARAM` tables only — analyst, deliberator, execution, forecaster, master,
portfolio_manager, provider, researcher, scanner. Their versions moved and no count did: no
clause was added, changed or proven.*

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
