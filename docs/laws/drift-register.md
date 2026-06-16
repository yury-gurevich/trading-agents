# Drift register — the correction worklist

Every place where a **law (intent)** and **reality (PRD / mission / code)** disagree is recorded here
once, with a stable `DRIFT-NN` ID, so we can set them back on course later. Fed by each agent's local
**Divergence Register**. See conventions §9.

**Kinds** — `PRD-fork` (law vs PRD, needs a forced decision) · `stale-doc` (PRD/mission out of date
vs a later decision) · `code-drift` (code diverged from intent) · `gap` (intent not yet built).
**Status** — `OPEN` (awaiting forced decision) · `DECIDED` (resolution chosen) · `CORRECTED`.

## Provider (`PROV`)

| ID | Law | Intent says | Reality says | Kind | Status / decision |
| --- | --- | --- | --- | --- | --- |
| DRIFT-001 | PROV-STA-01..04 | The cache is a transparent perf optimisation; not load-bearing. | Mission/PRD: the provider **owns the price cache** (a first-class fact store). | PRD-fork | **DECIDED D1** — load-bearing store; applied to law |
| DRIFT-002 | PROV-NEV-08 | Provider serves *raw* news; sentiment scoring is downstream. | `mission.md` listed **finbert** as a provider client. | stale-doc (vs ADR-0002) | **CORRECTED D2** — `mission.md` fixed; `NEV-08` added |
| DRIFT-003 | PROV-IN-06 | Fields = price, fundamentals, news, benchmark, regime. | `mission.md` also lists **FRED** (macro) and **EDGAR** (filings). | gap / scope | **DECIDED D3** — in-law, deferred; applied (`IN-06`) |
| DRIFT-004 | PROV-OUT-02 | Regime response = classification + its inputs. | PRD/mission: provider emits the regime-derived **policy inputs** (stop/target/holding defaults). | gap (enrich) | **CORRECTED** — adopted; `OUT-02` sharpened |
| DRIFT-005 | PROV-OUT-06 | Degradation = a quality record on the response (pull). | `mission.md`: provider also **emits** `market_data_degraded` (push). | gap (enrich) | **CORRECTED** — adopted; `OUT-06` added |
| DRIFT-006 | PROV-OUT-01 | Benchmark is just another **requested field** of a market-data request. | Code (S38) fetches the benchmark via a **separate** request to dodge a degraded-quality trip. | code-drift | OPEN — reconcile code to law at test time |
| DRIFT-007 | PROV-SEC-07 | Only capability-matrix-authorised callers may invoke the provider. | Unverified that the matrix actually gates data requests. | code-drift (verify) | OPEN — confirm at reconciliation |

## System-level

| ID | Question | Decision | Status |
| --- | --- | --- | --- |
| DRIFT-008 | Inter-agent hand-off: DB-mediated vs RabbitMQ-payload vs claim-check vs synchronous RPC. | **Event-driven pub/sub over Azure Service Bus, claim-check** (data in Neo4j, `ready: <ref>` events on the bus; logs on Event Hubs). Reversed an initial RPC choice on owner review; Azure-native per the lock-in commitment. | **RESOLVED** — ADR-0005 (supersedes ADR-0004); `PROV-TRG-01`/`OUT-01` updated (law v0.3). Kernel `MessageBus` → publish/subscribe is the system-wide consequence. |

| DRIFT-009 | DEP-FEED-01 / PROV-DEP-01 | The provider's keyless OHLCV feed (Stooq) is reachable and parseable. | **Stooq now serves a JS proof-of-work anti-bot interstitial**, not CSV; the provider's `urllib` client gets a 404. Finnhub daily candles are premium-only. **Only working OHLCV source is the Postgres `price_cache` fallback** (historical, to 2026-05). | dep-health / code-drift (real-probe finding) | OPEN — provider live-feed strategy needs a decision (see below) |

> **Live-feed strategy (open):** for the **test cycle**, seed the provider's durable store from Postgres
> `price_cache` (real OHLCV, satisfies `PROV-STA`/the store laws). For **production live data**, Stooq is
> out and Finnhub free has no daily candles — a working feed must be chosen (headless-browser Stooq is
> fragile; candidates: a paid feed, or another free source). Reinforces decision **D1** (load-bearing
> store) and the owner's "Postgres-as-fallback" guidance.

## Other agents

*Populated as each agent is authored and reconciled.*
