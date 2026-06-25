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
| DRIFT-006 | PROV-OUT-01 | Benchmark is just another **requested field** of a market-data request. | Code (S38) fetches the benchmark via a **separate** request to dodge a degraded-quality trip. | code-drift | **CORRECTED (S69)**: `DataRequest.benchmark_ticker` + `MarketData.benchmark` added; `taint=False` so degraded benchmark doesn't set `used_fallback` on the candidate quality; analyst uses `market.benchmark` directly. |
| DRIFT-007 | PROV-SEC-07 | Only capability-matrix-authorised callers may invoke the provider. | Unverified that the matrix actually gates data requests. | code-drift (verify) | **CORRECTED (S69)**: `caller_authorized` predicate + `allowed_callers` param in all three buses (`InProcessBus`, `CeleryBus`, `AzureServiceBusBus`); `AgentBase.bind` passes `capability.allowed_callers`; provider contract gates `get_market_data` to 5 callers and `get_regime` to 2 callers. |
| DRIFT-011 | PROV-IDM / PROV-STA | A same-day re-run **idempotently updates** the MarketData node (`ingest.py` keys it by window-end date). | Neo4j `_append_props` enforces provenance **immutability** — a property written once cannot be overwritten with a *different* value; a 2nd same-day run with a different universe → `ValueError: property 'snapshot' cannot be overwritten`. The in-memory store hid it (it allows overwrite). | code-drift (Neo4j-only; in-memory hid it) | **CORRECTED (0.35.01)** — keyed MarketData/RegimeContext by **run_id** (mirrors the pubsub path's `run_id or uuid` in `agent.py`; downstream follows the `INGESTED_BY`/`DERIVED_FROM` edge + derives the regime key from a new `run_id` prop). Proven: the full S&P-100 → Aura run now completes without collision. |
| DRIFT-012 | PROV-OUT-06 / ANLZ-IN | `used_fallback` flags genuinely-degraded data; the analyst bails on it. | A live S&P-100 run returned **clean OHLCV (99/99, no stale)** but `used_fallback=True` from `daily_move_sigma_anomaly` (a real big-mover trips the too-tight default sigma) **and optional-field faults** (`fundamentals/news/sectors/earnings_degraded` — Finnhub rate-limited at 99 per-ticker calls). The analyst then **rejected all 5 candidates** → zero trades. So optional *enrichment* failure (and one sigma outlier) blocks trading on otherwise-good OHLCV. | code-drift (over-taint, surfaced by live acceptance) | **CORRECTED (0.35.02)** — `_fetch_optional` never taints (only core OHLCV degradation blocks; faults still noted + routed); `max_daily_move_sigma` 4.0→8.0. **Proven: the clean S&P-100 → Aura run now PASSES** (5 positions opened; OBSERVATORY OK; ACCEPTANCE PASS). Layer-3 🟩. |
| DRIFT-014 | PROV-OUT-06 / ANLZ-IN | OHLCV quality is per-batch; a degraded batch blocks trading. | At **S&P-500 scale** the per-batch model **does not scale**: the `daily_move_sigma_anomaly` check is *pooled cross-sectional* and its taint is *batch-level*, so **one** name's >8σ move (or a split/glitch) among 503 sets `used_fallback` → the analyst rejects **every** candidate, including the clean survivors (`returned 503/503`, no stale, yet 0 scored). At larger N the chance of ≥1 outlier → 1, so the batch is ~always degraded → zero trades. | code-drift (per-batch quality doesn't scale; surfaced by the live S&P-500 acceptance) | **OPEN** — the S&P-500 run completed (Alpaca pulled 503/503 — the **data layer scales**) but `ACCEPTANCE FAIL`. Direction: **per-ticker quality** — *exclude* the anomalous ticker's bars (like `stale_tickers`) instead of tainting the batch, so the analyst scores the clean remainder. Also surfaced an efficiency follow-up: an **OHLCV-only fast mode** (the single-shot run makes 503×4 enrichment calls the acceptance doesn't need). |
| DRIFT-013 | PM-NEV-04 / PM-NEV-06 | The sector caps (dollar + name-count) bound concentration. | The same clean run opened **5 correlated names (4 semis + 1 bank)** with PM-NEV-06 **silently inactive** — `market.sectors` was empty (Finnhub `sectors_degraded`, now non-tainting per DRIFT-012), so every name's sector is `None` → both caps skip. The concentration guard is **data-dependent**; when sector data is absent it quietly does nothing. | code-drift (silent bypass, surfaced by live acceptance) | **CORRECTED (0.37.00).** *Visibility (0.36.00):* the bypass is now **loud** — a `sectors N/M classified (0 = caps INACTIVE)` line + a **`sector_coverage` WARN** via a new **advisory-severity** check (`severity="warn"` — surfaced, non-blocking; the PM acted correctly given absent data). *Robustness (0.37.00):* `sector_cache.resolve_sectors` treats sectors as **cached reference data** (not market data) — each ticker's sector is persisted once in the graph (`Sector` nodes, first-write-wins) and the universe's gaps are filled from the cache, so after the first successful fetch the caps **always have data even when Finnhub rate-limits**. Proven in-memory (a live-empty run fills 2/2 from a warmed cache). *Operational note:* the cache must warm once per ticker (a paced run where the live fetch succeeds); a cold cache still shows the warn. No PM/law change — the existing PM-NEV-04/06 just stop starving. **PROVEN LIVE (2026-06-25):** a paced S&P-100 run cached all **99/99** sectors in Aura (Finnhub returns granular industries — `Semiconductors` is its own bucket); a subsequent **single-shot** run (live sectors rate-limited again) still showed **`sectors 99/99 classified`** from the cache, `OBSERVATORY OK`, and **PM-NEV-06 fired** — `INTC SKIP sector_name_count` (at cap=2; the shipped cap=3 correctly allows the run's 3 semis). |

## System-level

| ID | Question | Decision | Status |
| --- | --- | --- | --- |
| DRIFT-008 | Inter-agent hand-off: DB-mediated vs RabbitMQ-payload vs claim-check vs synchronous RPC. | **Event-driven pub/sub over Azure Service Bus, claim-check** (data in Neo4j, `ready: <ref>` events on the bus; logs on Event Hubs). Reversed an initial RPC choice on owner review; Azure-native per the lock-in commitment. | **RESOLVED** — ADR-0005 (supersedes ADR-0004); `PROV-TRG-01`/`OUT-01` updated (law v0.3). Kernel `MessageBus` → publish/subscribe is the system-wide consequence. |

| DRIFT-009 | DEP-FEED-01 / PROV-DEP-01 | The provider's keyless OHLCV feed (Stooq) is reachable and parseable. | **Stooq is anti-bot-blocked** (PoW interstitial → 404); **Finnhub `/candle` is premium** (403); **FMP free is only ~87 curated symbols** (PG/HD → 402), not the full S&P 500. **Full-universe live fix:** **Tiingo free** (500 symbols/month, 30+ yrs, real-time IEX) covers the S&P 500; **Alpaca free** = full-US data **+ broker**. | dep-health / code-drift (real-probe finding) | **CORRECTED** — ADR-0006 + **S44 shipped**: `TiingoDataSource` is the live full-S&P-500 default (`market_source_from_settings` OHLCV→Tiingo; `orchestration/bindings.py` re-pointed off broken Stooq). FMP retained as validation/failover; Alpaca broker + a failover wrapper are the remaining follow-ups. |

> **Live OHLCV — CORRECTED 2026-06-16 (ADR-0006; S44 shipped).** No keyless feed serves the full
> S&P 500 live: Stooq is anti-bot-blocked, Finnhub `/candle` is premium, and **FMP free is a curated
> ~87-symbol subset** (empirically PG, HD → `402`). **Two free keyed tiers do, and both keys are now
> live (in `.env`):** **Tiingo** (`TIINGO_API_KEY`; free = 500 unique symbols/month — covers the
> S&P 500 — 30+ yrs history, real-time IEX) is the **primary full-universe OHLCV feed**; **Alpaca**
> (`ALPACA_API_KEY/SECRET`; free full-US data **and** the broker) is the **broker boundary + secondary/
> failover feed** (one vendor for DEP-FEED + DEP-BROKER). **Built:** `agents/provider/fmp.py`
> **Shipped (S44):** `agents/provider/tiingo.py` `TiingoDataSource` (OHLCV only; Z-suffixed ISO date
> sliced to `YYYY-MM-DD`); `market_source_from_settings` routes OHLCV→Tiingo, fundamentals/news→Finnhub;
> `orchestration/bindings.py` default re-pointed off broken Stooq; `tiingo_*` settings; unit tests (620
> passed, 100.00%). `FMPDataSource` retained as the **validation sub-universe / failover**. **Remaining
> follow-ups:** a `FailoverDataSource` wrapper (Tiingo→FMP→Alpaca) and `AlpacaDataSource` + the Alpaca
> broker adapter. Postgres `price_cache` stays the raw historical backtest fallback. Confirms decision
> **D1**; Stooq retired as default; no scraping.

## Portfolio Manager (`PM`)

| ID | Law | Intent says | Reality says | Kind | Status / decision |
| --- | --- | --- | --- | --- | --- |
| DRIFT-010 | PM laws.md changelog | `INDEX.md` + `CLAUDE.md` + memory record PM as **LOCKED v1 (S70)**. | PM `laws.md` changelog footer still read *"v0 — drafted… Not yet locked"* (stale; never updated at the S70 lock). | stale-doc | **CORRECTED** (cage audit, 2026-06-25): footer reconciled to v1 + the PM-NEV-06 amendment (v1.1). |

## Other agents

*Populated as each agent is authored and reconciled.*
