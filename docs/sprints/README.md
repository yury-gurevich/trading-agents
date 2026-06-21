# Sprints — handover to the coding agent

This folder holds **self-contained sprint plans**. Each is a handover a cold-start
coding agent can execute end to end without further context.

## Roles

- **Planning agent (owner of this folder, the PRD, the build plan, and STATE).**
  Decides *what* to build next and *why*, writes the sprint handover, reviews the
  result, and updates `docs/STATE.md` + `docs/build-plan.md` progress. Does not
  write production code.
- **Coding agent.** Executes exactly one active sprint plan: writes the code and
  tests, keeps the quality gate green, and hands back a short report. Stays within
  the sprint's scope; anything out of scope goes back to the planning agent.

## How a sprint runs

1. Planning agent writes `sprint-NN-<slug>.md` here and marks it active in STATE.
2. Coding agent branches `sprint-NN-<slug>`, implements the steps, gets the gate
   green, pushes, and reports back (files changed, coverage %, decisions/notes).
3. Planning agent reviews, merges to `main`, and updates STATE + build-plan status.

## Non-negotiable guardrails (every sprint)

These hold regardless of the sprint's specifics:

- **The one rule.** No agent imports another agent. The kernel imports nothing from
  `contracts`/`agents`. Agents talk only via typed messages. `import-linter` enforces.
- **Small files.** Every module < 200 lines (warn at 150). Split, don't grow.
- **Coding-agent header.** Every module's docstring declares `Agent:` and `Role:`
  (and `External I/O:` where relevant). Enforced by `scripts/check_module_header.py`.
- **No magic numbers.** Any value influencing processing or a forecast is declared
  with `kernel.tunable(..., why="...")` — justified and bounded — never a bare literal.
- **Faults, not silent failure.** Wrap fallible work in `kernel.fault_boundary`;
  errors are redirected with provenance, never swallowed.
- **Green before handback.** `make ci` must pass (ruff, format, mypy, import-linter,
  size + header guards, pytest at/above the coverage floor). Never lower the floor;
  raise it if measured coverage climbs.
- **Stay in scope.** Build only what the active sprint plan lists. Flag anything else.

## Validation (the gate)

```bash
make ci          # full local gate, mirrors GitHub CI
# or individually:
uv run ruff check . && uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
uv run python scripts/check_module_header.py kernel contracts agents scripts
uv run pytest
```

## Index

| Sprint | Goal | Status |
| --- | --- | --- |
| [sprint-01](sprint-01-kernel-runtime.md) | Kernel runtime: in-process bus + AgentBase | **shipped** |
| [sprint-02](sprint-02-persistence.md) | Relational persistence adapter + migrations | **shipped** (superseded by ADR-0001) |
| [sprint-03](sprint-03-neo4j-store.md) | Neo4j GraphStore: retire relational adapter, graph spine | **shipped** |
| [sprint-04](sprint-04-provider-agent.md) | Provider agent: first real agent (data boundary + provenance) | **shipped** |
| [sprint-05](sprint-05-scanner-agent.md) | Scanner agent: first agent-to-agent call (universe → ranked candidates) | **shipped** |
| [sprint-06](sprint-06-analyst-agent.md) | Analyst agent: scored recommendations (closes the P2 slice) | **shipped** |
| [sprint-07](sprint-07-distributed-bus.md) | Distributed (Celery) bus: second MessageBus backend (P1 exit) | **shipped** |
| [sprint-08](sprint-08-observability-adapter.md) | Observability: kernel metrics adapter (throughput/latency/fault-rate) | **shipped** |
| [sprint-09](sprint-09-portfolio-manager.md) | Portfolio manager: sized, risk-checked order intents (starts P3) | **shipped** |
| [sprint-10](sprint-10-hardening.md) | Audit-truth & rigor hardening (rejection evidence, contract validators, graph/Neo4j rigor) | **shipped** |
| [sprint-11](sprint-11-execution.md) | Execution agent: idempotent broker boundary (paper stage, fills) | **shipped** |
| [sprint-12](sprint-12-monitor.md) | Monitor agent: open positions from fills, stop/target/time exits | **shipped** |
| [sprint-13](sprint-13-reporter.md) | Reporter agent: run snapshot + per-trade narrative (P3 exit) | **shipped** |
| [sprint-14](sprint-14-dispatcher.md) | Dispatcher: event-driven daily loop on both bus backends (P4 begins) | **shipped** |
| [sprint-15](sprint-15-supervisor.md) | Scheduler + supervisor message lineage (P4 exit) | **shipped** |
| [sprint-16](sprint-16-operator.md) | Operator agent: intent parsing + model-call ledger (P5 begins) | **shipped** |
| [sprint-17](sprint-17-supervisor-gate.md) | Supervisor capability gate + hard-NO surface (P5 exit) | **shipped** |
| [sprint-18](sprint-18-surfaces-cli.md) | Surfaces foundation + CLI: resolve_flag fix, query projections, terminal interface (P6 begins) | **shipped** |
| [sprint-19](sprint-19-list-nodes-lifecycle.md) | GraphStore list_nodes (Neo4j gap fix) + position lifecycle + pending-flags view (P6 continues) | **shipped** |
| [sprint-20](sprint-20-narrative-approve.md) | Trade narrative display + approve command (cli narrative + cli approve, P6 continues) | **shipped** |
| [sprint-21](sprint-21-incidents-explain-p6-exit.md) | Incident view + explain on demand + P6 exit test (P6 closes) | **shipped** |
| [sprint-22](sprint-22-mcp-tool-binding.md) | MCP tool-binding: operator + supervisor tools over Model Control Protocol (P1 closes) | **shipped** |
| [sprint-23](sprint-23-p7-researcher.md) | Researcher agent: propose bounded parameter changes + proposals surface + P7 exit test (P7 begins) | **shipped** |
| [sprint-24](sprint-24-p8-stage-gate.md) | Stage gate machinery: evidence-based promotion, StageTransition nodes, read-only cli stage (P8 begins) | **shipped** |
| [sprint-25](sprint-25-p8-market-pack.md) | Stage command wiring (cli stage promote → supervisor gate) + MarketPack abstraction + P8 exit test (P8 closes) | **shipped** |
| [sprint-26](sprint-26-p9-observability.md) | MeteredFaultSink wiring + P9 exit test + observability.md docs (P9 closes) | **shipped** |
| [sprint-27](sprint-27-p10-curator-datasets.md) | Curator agent: dataset assembly by provenance traversal, versioned splits, cli datasets (P10 begins) | **shipped** |
| [sprint-28](sprint-28-p10-training-trigger.md) | Curator training trigger: deterministic baseline predictor + frozen evidence, advisory-only, cli predictors (P10 training half) | **shipped** |
| [sprint-29](sprint-29-p10-predictor-registry.md) | Curator predictor registry: promote_predictor evidence gate + operator approval + PredictorPromotion audit (P10 exit) | **shipped** |
| [sprint-30](sprint-30-p11-analyst-technical-core.md) | Analyst technical scoring core: pure-Python RSI/MACD/Bollinger/SMA/EMA + band rules + composite (P11 begins) | **shipped** |
| [sprint-31](sprint-31-p11-analyst-oscillators.md) | Analyst oscillators + volatility: ATR/Stochastic/Williams %R/Choppiness folded into the composite (P11 cont.) | **shipped** |
| [sprint-32](sprint-32-p11-analyst-volume-event.md) | Analyst volume/event: OBV + golden cross + RSI-2 folded into the composite (P11 cont.) | **shipped** |
| [sprint-33](sprint-33-p11-analyst-patterns.md) | Analyst patterns/smoothing/calendar: Nadaraya-Watson kernel + geometric patterns + turnaround → composite up to 15 indicators (P11 cont.) | **shipped** |
| [sprint-34](sprint-34-provider-fundamentals.md) | Provider fundamentals feed: Finnhub /stock/metric → MarketData.fundamentals (unblocks analyst fundamental scoring) (P11 cont.) | **shipped** |
| [sprint-35](sprint-35-analyst-fundamental-scoring.md) | Analyst fundamental scoring: 8-metric pillar blended with technical into the confidence gate (P11 cont.) | **shipped** |
| [sprint-36](sprint-36-provider-news-feed.md) | Provider news feed: Finnhub /company-news → MarketData.news per-ticker headlines (feeds the analyst sentiment pillar) (P12) | **shipped** |
| [sprint-37](sprint-37-analyst-sentiment-pillar.md) | Analyst sentiment pillar: deterministic Loughran–McDonald lexicon as the binding third pillar in the renormalised blend (P12 champion) | **shipped** |
| [sprint-38](sprint-38-analyst-relative-strength.md) | Analyst relative strength: benchmark-relative momentum blended into the technical pillar (0.8/0.2); separate fault-tolerant benchmark fetch (P11) | **shipped** |
| [sprint-39](sprint-39-analyst-signal-diversity.md) | Analyst signal-diversity selection: surface the top pillar-diverse signals in the recommendation rationale (explanatory, no score change) (P11) | **shipped** |
| [sprint-40](sprint-40-pm-reward-risk.md) | Portfolio manager reward/risk gate: reject orders whose target_pct/stop_pct is below min_reward_risk_ratio (P11) | **shipped** |
| [sprint-41](sprint-41-reporter-trade-outcomes.md) | Reporter: profit-factor and expectancy over stop/target-closed positions; new `domain/trade_outcomes.py` (P11) | **shipped** |
| [sprint-43](sprint-43-monitor-realized-pnl.md) | Monitor realized PnL on close (`pnl_cents` on CloseDecision) — accuracy upgrade so the reporter can use real $ PnL across all triggers (P11) | **queued** (after S41) |
| [sprint-44](sprint-44-provider-tiingo-feed.md) | Provider Tiingo OHLCV feed: `TiingoDataSource` (full-S&P-500 live, ADR-0006) → re-point `market_source_from_settings` + `bindings.py` default off broken Stooq (closes DRIFT-009) | **shipped** |
| [sprint-45](sprint-45-execution-alpaca-broker.md) | Execution Alpaca paper broker: `AlpacaBroker` behind the `Broker` port (real fills, client_order_id idempotency) + `broker_from_settings` default swap (ADR-0006, DEP-BROKER) | **shipped** |
| [sprint-46](sprint-46-analyst-sentiment-reading.md) | Persisted `SentimentReading` node: champion lexicon reading per scored ticker (incl. rejected) for scorecard alignment; analyst `owns_graph` += SentimentReading (P12 item 2) | **shipped** |
| [sprint-47](sprint-47-provider-sentiment-feed.md) | Provider serves Alpha Vantage vendor sentiment into `MarketData.sentiment` via `DataSource.fetch_sentiment` (provider CONTRACT 0.2.0; the analyst shadow-reading is next) (P12) | **shipped** |
| [sprint-48](sprint-48-analyst-provider-sentiment-reading.md) | Analyst persists the provider-sentiment shadow reading (`scorer="provider"` `SentimentReading`, aligned to lexicon, never gates) — completes the provider-sentiment challenger (P12) | **shipped** |
| [sprint-49](sprint-49-forecaster-finbert-runtime.md) | Forecaster agent's first runtime: FinBERT sentiment shadow scorer behind a model Protocol (torch optional + lazily imported); persists `ShadowPrediction` (shadow, 0-1 aligned) + `Model`; `scorecard` never promotion-eligible — the trinity's 3rd leg (P12) | **shipped** |
| [sprint-50](sprint-50-scanner-beta-cap.md) | Scanner beta computation + beta-cap filter: fault-tolerant benchmark fetch, pure `compute_beta` (cov/var of aligned returns), drop candidates with `beta > max_beta`; additive + dormant on thin history (P11) | **shipped** |
| [sprint-51](sprint-51-provider-sector-feed.md) | Provider sector feed: `DataSource.fetch_sectors` (Finnhub `/stock/profile2` → `finnhubIndustry`), field-gated into `MarketData.sectors` (CONTRACT 0.3.0); the substrate the PM sector cap consumes next (P11) | **shipped** |
| [sprint-52](sprint-52-pm-sector-cap.md) | PM sector-concentration cap: reject orders that would push their sector over `max_sector_pct` of portfolio value (reason `sector_concentration`); consumes `MarketData.sectors`, additive + dormant on unknown sectors — the PM risk-gate pair (twin of S40) (P11) | **shipped** |
| [sprint-42](sprint-42-provider-earnings-feed.md) | Provider earnings-calendar feed: `DataSource.fetch_earnings` (Finnhub `/calendar/earnings` → next upcoming date), field-gated into `MarketData.earnings` (CONTRACT 0.4.0); field-gates refactored into `market_fields.py`; the substrate the scanner earnings-window exclusion consumes next (P11) | **shipped** |
| sprint-53 (no doc; see [ADR-0007](../decisions/0007-container-per-agent-master-bootstrap.md)) | Provider laws: `CAP` + `PARAM` sections (ADR-0007 backfill) added to `agents/provider/laws/laws.md` — runtime capability declaration + 20-entry parameter table; the pattern for the 11 remaining agent law backfills | **shipped** |
| [sprint-54](sprint-54-scanner-earnings-exclusion.md) | Scanner earnings-window exclusion: requests `"earnings_calendar"`, drops candidates whose next earnings is within `earnings_exclusion_days` of the scan as-of (`earnings_window`); consumes `MarketData.earnings`, additive + dormant — completes the scanner deterministic port; version 0.1.0→0.2.0 (P11) | **shipped** |
| [sprint-43](sprint-43-monitor-realized-pnl.md) | Monitor realized PnL on close: pure `realized_pnl_cents=(exit−entry)×qty`; `CloseDecision.pnl_cents` (contract 0.2.0 + node prop), holds `None`; decision logic extracted to `decide.py`; version 0.2.0→0.3.0 — the realized-outcome substrate for the reporter $-PnL re-point (P11) | **shipped** |
| [sprint-55](sprint-55-reporter-realized-pnl-repoint.md) | Reporter re-point to real $ PnL: `collect_trade_outcomes` reads `pnl_cents` off close decisions → dollar `profit_factor`/`expectancy_cents` across all triggers incl. time (`expectancy_pct→expectancy_cents`, no contract change); version 0.3.0→0.4.0 — **closes P11** | **shipped** |
| [sprint-56](sprint-56-analyst-lm-master-dictionary.md) | Analyst champion upgrade: load the full Loughran–McDonald master dictionary (Positive 354, Negative 2355; vendored under `agents/analyst/domain/data/`) unioned with the curated headline terms LM omits (beat/surge/plunge/...); polarity-disjoint, `score_sentiment` unchanged; version 0.4.0→0.5.0 (P12) | **shipped** |
| [sprint-57](sprint-57-forecaster-sentiment-scorecard.md) | Forecaster sentiment scorecard harness: `sentiment_scorecard` capability comparing lexicon/provider/FinBERT readings vs injected forward returns (Pearson + 2-regressor OLS, per-scorer IC + FinBERT incremental IC); reads readings from the graph, returns injected; advisory (never promotion-eligible); forecaster CONTRACT 0.2.0; version 0.5.0→0.6.0 (P12) | **shipped** |
| [sprint-58](sprint-58-forecaster-lightgbm-shadow.md) | Forecaster LightGBM price/return shadow signal (qlib Phase Q1): `ReturnModel` port + lazy `lightgbm` adapter + pure feature builder + provider OHLCV request → `ShadowPrediction` (shadow, never gates); `lightgbm`-direct (pyqlib is 3.13-incompatible on Python 3.13); CONTRACT 0.2.0→0.3.0; version 0.6.0→0.7.0 (Q1) | **shipped** |
| [sprint-59](sprint-59-forecaster-lgbm-training-scorecard.md) | Forecaster LightGBM training pipeline + return IC scorecard (qlib Phase Q1 follow-on): `build_label_rows` + walk-forward `split_rows` + `train_and_save` offline script; `return_scorecard` capability (IC + hit_rate + directional breakdown vs injected forward returns); CONTRACT 0.3.0→0.4.0; version 0.7.0→0.8.0 | **shipped** |
| [sprint-60](sprint-60-p14-kernel-pubsub.md) | P14 step 1 — Kernel pub/sub: `MessageBus.publish/subscribe` + `InProcessBus` fan-out; `ReadyEvent` model; both-mode bus green | **shipped** |
| [sprint-61](sprint-61-p14-claim-check.md) | P14 step 2 — Kernel claim-check primitive: `claim_check_write/read` over the graph; `ReadyEvent` published after each write | **shipped** |
| [sprint-62](sprint-62-p14-provider-pubsub.md) | P14 step 3 — Provider pub/sub dual-mode: `bind()` subscribes to `run.trigger`, publishes `MarketData` via claim-check | **shipped** |
| [sprint-63](sprint-63-p14-scanner-analyst-pubsub.md) | P14 step 4 — Scanner + analyst pub/sub dual-mode: `scan.candidates.ready` → `analysis.recommendations.ready` chain | **shipped** |
| [sprint-64](sprint-64-p14-pm-execution-pubsub.md) | P14 step 5 — PM + execution pub/sub dual-mode: `analysis.recommendations.ready` → `portfolio.orders.ready` → `execution.fills.ready`; `pm_run_id` threading begins | **shipped** |
| [sprint-65](sprint-65-p14-monitor-reporter-pubsub.md) | P14 step 6 — Monitor + reporter pub/sub dual-mode: `execution.fills.ready` → `monitor.decisions.ready` → `report.snapshot.ready`; whole pipeline event-driven in-process | **shipped** |
| [sprint-66](sprint-66-p14-dispatcher-trigger-emitter.md) | P14 step 7 — Dispatcher → trigger-emitter: `execute_run` publishes `run.trigger`, subscribes `report.snapshot.ready`; step sequencing removed; dispatcher unit + daily-loop tests rewritten | **shipped** |
| [sprint-67](sprint-67-p14-azure-servicebus-backend.md) | P14 step 8 — Azure Service Bus backend: `AzureServiceBusBus` + `AzureServiceBusSettings`; in-process shim for RPC; `# pragma: no cover` on I/O path; parity test skips without creds; version 0.8.0→0.9.0; P14 complete | **shipped** |
| [sprint-68](sprint-68-analyst-alpha158-pillar.md) | Analyst Alpha158 pillar (qlib Phase Q2): 22-field time-series subset (ROC/STD/MAX/MIN/IMAX/IMIN) → cross-sectional z-score → logistic 0-100 fifth pillar; `alpha158_pillar_weight=0.00` (off by default); pyqlib-free (3.13 constraint); version 0.9.0→0.10.0 | **shipped** |
| [sprint-69](sprint-69-provider-law-cycle.md) | Provider law cycle — lock the template: DRIFT-006 corrected (benchmark as first-class `DataRequest` field + `taint=False` isolation); DRIFT-007 corrected (caller-authz gate in all 3 buses + provider capability matrix); law-ID citation pass (7 test files); test-plan 23/43 green; provider laws LOCKED v1; template locked for copying to 11 agents; version 0.10.0→0.11.0 | **shipped** |
| [sprint-70](sprint-70-per-agent-law-backfill.md) | Per-agent law backfill (4 of 11): scanner/analyst/PM/execution laws authored from first principles → citation pass (12 test files) → laws LOCKED v1; `test_scanner_explain.py` split; 95 green clauses added | **shipped** |
| [sprint-71](sprint-71-per-agent-law-backfill.md) | Per-agent law backfill (remaining 7 of 11): monitor/reporter/forecaster/operator/supervisor/curator/researcher laws authored from first principles → citation pass → 7 test-plan.md files → all 7 laws LOCKED v1; 124 green clauses added | **shipped** |
| [sprint-72](sprint-72-system-prompt-tunable.md) | ADR-0010 immediate close: `system_prompt` tunable wired into `OperatorSettings` + `_interpret_command`; pre-declared on `ForecasterSettings`; law PARAM sections updated | **shipped** |
| [sprint-73](sprint-73-p15-master-agent.md) | P15 foundation: `MasterAgent` (start/activate/drain) + `DEFAULT_GRANTS` privilege table + `contracts/master.py` (EHLOMessage/ACTIVATEMessage/DRAINMessage) + 11 tests (100%); per-agent Dockerfiles (13 images); multi-service docker-compose.yml; master laws LOCKED v1 (MST, 10 clauses green); RSA + Key Vault deferred to S74 | **shipped** |
| [sprint-74](sprint-74-p15-rsa-entrypoints.md) | P15 RSA signing + agent entrypoints: `kernel/crypto.py` (RSA-PSS sign/verify/generate), `kernel/bootstrap.py` (activate\_agent + injectable \_send), `agents/master/http_server.py` (handle\_health/handle\_ehlo pure), `agents/master/entrypoint.py` (build\_app testable + main), 12 trading-agent entrypoints; 951 tests 100% coverage; version 0.11.0→0.12.0; Key Vault deferred to S75 | **shipped** |
| [sprint-75](sprint-75-p15-key-vault.md) | P15 Key Vault secret distribution: `SecretStore` Protocol + `NullSecretStore` + `EnvVarSecretStore` + `AzureKeyVaultSecretStore`; `AGENT_SECRETS` entitlement table + `resolve_config`; `MasterAgent.activate()` populates `config` with per-agent minimum-privilege secrets; DRIFT-002 resolved; 971 tests 100% coverage; version 0.12.0→0.13.0 | **shipped** |
| [sprint-76](sprint-76-p15-ghcr-deploy.md) | P15 GHCR build pipeline + Container Apps deploy: GitHub Actions matrix build → GHCR images; Key Vault provisioning + secret seeding; deploy-agents workflow (master first, then parallel); `trading-agents-kv` live; scanner boots + EHLO confirmed in log stream | **shipped** |
| [sprint-77](sprint-77-credential-naming.md) | Canonical credential-naming reconciliation: align `secret_map.py` output keys to match agent settings `env_prefix` (PROVIDER\_/EXECUTION\_/OPERATOR\_ prefixes); fix `.env` FNP\_ typo; version 0.16.1 (PATCH) | **planned** |
| [sprint-78](sprint-78-provider-ingestor.md) | Provider as standalone graph-ingestor: replaced `idle_loop()` with real ingest loop; `build_graph_from_env()` kernel helper; provider writes market data to graph; version 0.17.00 (MINOR) | **shipped** |
| [sprint-79](sprint-79-agent-work-loops.md) | Agent work loops — vertical slice (DL-08b): provider persists full `MarketData` payload; scanner reads it from the graph (`poll.py` `find_pending`+`scan_market_node`, `SCANNED_BY` edge) instead of bus RPC; `kernel/work_loop.py` reusable loop; scanner drops idle_loop. analyst→reporter deferred to S80; version 0.18.00 (MINOR) | **shipped** |
| [sprint-80](sprint-80-analyst-graph-pull.md) | Analyst graph-pull (scanner→analyst): provider also persists full `RegimeContext`; scanner persists full `CandidateSet` on `ScanRun`; analyst reads CandidateSet+MarketData (DERIVED_FROM)+RegimeContext from graph (`agents/analyst/poll.py`), scoring core extracted to `agents/analyst/run.py` shared by bus+graph paths; analyst drops idle_loop. PM→reporter deferred to S81; version 0.19.00 (MINOR) | **shipped** |
| [sprint-81](sprint-81-pm-graph-pull.md) | PM graph-pull (analyst→PM): analyst persists full `RecommendationSet` on `AnalystRun`; PM reads it + MarketData (ANALYZED_BY→ScanRun→DERIVED_FROM) + same-day RegimeContext from graph (`agents/portfolio_manager/poll.py`), sizing/risk core extracted to `agents/portfolio_manager/run.py` shared by bus+graph paths; PM drops idle_loop, `EVALUATED_BY` edge. execution/monitor/reporter deferred to S82; version 0.20.00 (MINOR) | **shipped** |
| [sprint-82](sprint-82-execution-monitor-reporter-graph-pull.md) | Execution+monitor+reporter graph-pull (closes DL-08 end-to-end): PM persists full `OrderIntentSet` on `PMRun`; execution adds an `ExecutionRun` anchor + `poll.py`/`run.py` (`PMRun`→`EXECUTED_BY`); monitor reads close prices from graph `MarketData` instead of provider bus RPC + `poll.py` (`ExecutionRun`→`MONITORED_BY`); reporter gets a `poll.py` trigger over `build_snapshot` (`MonitorRun`→`REPORTED_BY`); all three drop idle_loop. Permanent graph store deferred; version 0.21.00 (MINOR) | **planned** |
