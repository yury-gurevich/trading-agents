# Project State

**Last updated:** 2026-06-16 — **Sprint 45 shipped** (execution Alpaca paper broker: `AlpacaBroker`
behind the `Broker` port, `client_order_id` idempotency, `broker_from_settings` default swap — DEP-BROKER,
ADR-0006); **Sprint 44 shipped** (provider Tiingo live OHLCV feed — closes DRIFT-009); **S41 planned**
(reporter profit-factor + expectancy); S37 (analyst sentiment pillar) queued. 628 tests at 100.00%.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**S44 shipped — provider Tiingo live OHLCV feed (ADR-0006, DRIFT-009 CORRECTED).** The runtime default
source was broken (`StooqDataSource` anti-bot-blocked) and FMP free covers only ~87 symbols; S44 added
`agents/provider/tiingo.py` `TiingoDataSource` (full S&P 500, free 500 sym/mo; Z-suffixed ISO date
sliced to `YYYY-MM-DD`), routed `market_source_from_settings` OHLCV → Tiingo, and re-pointed the
`orchestration/bindings.py` default off Stooq. No contract change; FMP retained as validation/failover.
Feeds/broker strategy: `docs/decisions/0006-market-data-feed-strategy.md`.

**S45 shipped — execution Alpaca paper broker (DEP-BROKER, ADR-0006).** `agents/execution/alpaca.py`
`AlpacaBroker` behind the existing `Broker` port (market order, `client_order_id` idempotency with
duplicate→fetch replay, real fills/positions); `broker_from_settings` builder; `bindings.py` default
swap (Alpaca paper when keyed, else `PaperBroker` — unit gate stays network-free). Settings read the
unprefixed `.env` Alpaca names via `AliasChoices`+`populate_by_name`. No contract change. Unlocks the
Alpaca paper P/L + "fake purchases" harness (memory `alpaca-paper-broker`). **Follow-ups:** real
DEP-BROKER probe (submit→fill→cancel); pending→filled reconciliation across sessions; data-side
`FailoverDataSource` + `AlpacaDataSource`. **Next coding sprint:** P12 S37 (analyst lexicon pillar)
resumes — *unless* the owner prioritises a follow-up above.

**P12 status: news feed live (S36 shipped), lexicon pillar queued (S37).** S36 shipped:
`fetch_news` on `FinnhubDataSource` (twin of S34 fundamentals) — `MarketData.news` now populated
with per-ticker Finnhub `/company-news` headlines, field-gated with the same fault boundary and
`news_degraded` quality note. **Sprint 37 — analyst lexicon pillar** (the deterministic
Loughran–McDonald lexicon champion, `sentiment_weight` 0.20, folded into the renormalised
three-pillar blend; `Recommendation.sentiment_score` set; no contract change) is the next coding
sprint. Shipping S37 starts live news accrual (real headlines scored onto persisted
`Recommendation.sentiment_score`). **P11 analyst-side complete** (S30–S35 + S38–S39); **P11 PM
gate done** (S40 reward/risk). P11 remaining: reporter profit-factor + expectancy (S41, planned),
scanner beta + earnings (S42), PM sector cap. 611 tests, floor 100.00. Spec sources:
`docs/decisions/0002-sentiment-champion-challenger.md`, memory `v1-deterministic-port-gaps.md`.

## Next

- **P12 — Sentiment (champion–challenger)**, in order: **S36 provider news feed** (**shipped**) →
  **S37 analyst lexicon pillar** (planned; binding, `sentiment_weight` 0.20; reading rides on
  `Recommendation.sentiment_score`, no new node/contract change) →
  **provider-sentiment** challenger (Finnhub `/news-sentiment`, shadow) → **forecaster/FinBERT**
  agent (advisory, dep isolated, `ShadowPrediction` + `model_version`) → **relationship/scorecard
  harness** (align A/B/F + forward returns; promote via P10 gate). Spec: ADR-0002. **Postgres checked
  2026-06-15:** the deprecated v1 store (test-only, not a product dependency) has 5 yr S&P-500 daily
  OHLCV (`price_cache`, forward-return fixture) but **empty news tables** → the harness needs a live
  news-accrual runway (S36 feed scored forward), not a backfill.
- **P11 remaining** (non-analyst deterministic gaps): **S41 — reporter profit-factor + expectancy**
  (planned; `domain/trade_outcomes.py`, %-based from trigger, time-exits excluded, no contract change)
  → **S43 — monitor realized PnL** (**queued, blocked until S41 merges**; `pnl_cents` on `CloseDecision`,
  contract 0.2.0) → **reporter re-point** to real $ PnL across all triggers (replaces S41's
  approximation) → scanner (beta + earnings, S42) → PM **sector-concentration cap** (needs a `sector`
  field — larger plumbing). **Decision 2026-06-16** (parallel-agent collision): the external coding
  agent planned S41 (reporter, %-based); we ship that now and add real PnL after — see memory
  `realized-pnl-sequencing`. **Done:** analyst scoring + **PM reward/risk gate (S40)**. Sequenced spec:
  memory `v1-deterministic-port-gaps.md`. Note for P12 S37: the sentiment pillar adds a `score_candidate`
  param **and** should add `"sentiment"` to the S39 signal-selection weights map (mechanical).
- **P13 — Cross-asset & macro signal graph** (later): sector contagion + signed tariff/sanction event
  propagation over Neo4j; contingent on P12 + the data runway. Spec: ADR-0002.
- Build-when-needed: RAG vector index (deferred; no sprint planned).

## Workflow

The planning agent writes sprint handovers and maintains documentation
and progress; a coding agent implements one active sprint at a time on its
own branch and hands back. See `docs/sprints/README.md`.

## Parked

- (none)

## Shipped

- **Sprint 36 — Provider: news feed** (P12; first P12 sprint). New `fetch_news` on
  `FinnhubDataSource` (`fundamentals.py`, extended in-place at 166L) + `_download_news` /
  `_parse_news` (pure parser: strips non-string/empty/missing headlines, caps at
  `max_news_per_ticker`, never raises). Two new tunables (`finnhub_news_lookback_days` 7,
  `max_news_per_ticker` 20). `DataSource` Protocol gains `fetch_news`; `FakeDataSource` adds
  `news` fixture + `fail_news`; `StooqDataSource` stubs it. `CompositeDataSource` delegates news
  to the Finnhub source. `get_market_data` field-gates `"news"` with its own `fault_boundary` →
  `{}` + `"news_degraded"` quality note on fault. **No contract change** (CONTRACT 0.1.0,
  `owns_graph`/`external_io` untouched); **no new dependency** (stdlib urllib/json only). OHLCV
  and fundamentals callers untouched — no re-pin. 611 tests, floor 100.00.
- **Sprint 40 — Portfolio manager: reward/risk gate** (P11; implemented directly). New PM tunable
  `min_reward_risk_ratio` (1.5) and a gate in `domain/risk.py`: because v2 carries percentages, the
  reward/risk ratio reduces to `target_pct / stop_pct` (entry cancels). Extracted `_effective_pcts`
  (recommendation's suggested stop/target, else regime defaults) shared by the gate and the order
  intent; `_reward_risk_rejection` rejects `invalid_stop_loss` (stop_pct ≤ 0) and `reward_risk_below_min`
  (ratio < min). `evaluate_recommendations` runs it after sizing/cash/position checks. Default 1.5 passes
  the regime default 2.0, so no existing approval re-pinned **except** the deliberate-zero-stop audit
  test (a 0 % stop is now correctly rejected → retargeted to a valid explicit policy). **No contract
  change.** 595 tests, floor 100.00. Sector cap deferred (needs sector plumbing).
- **Sprint 38 — Analyst: relative strength** (P11; implemented directly). New pure
  `domain/relative_strength.py` (`compute_relative_strength` — candidate minus benchmark trailing
  return over `rs_window`; `score_relative_strength` — bands `>5→80 / >0→60 / >−5→40 / else→20`).
  `score_candidate` gained a `benchmark_bars` arg and `_apply_relative_strength` blends RS **into the
  technical pillar** at `0.8·technical + 0.2·rs` (v1's design — not a 4th composite pillar); absent/
  short benchmark history skips it → technical unchanged → **no re-pin**. New
  `provider_client.request_benchmark_bars` fetches the benchmark (`benchmark_ticker`, default `SPY`) in
  a **separate, fault-tolerant** request so a missing benchmark forgoes RS instead of degrading
  candidate data; analyst `_score` threads the bars through. Tunables: `benchmark_ticker`, `rs_window`
  (20), `relative_strength_weight` (0.20). Fixed the stateful `ReboundingDataSource` test fixture to
  ignore benchmark-only probes. **No contract change** (analyst 0.1.0). 592 tests, floor 100.00.
- **Sprint 39 — Analyst: signal-diversity selection** (P11; implemented directly on request). New pure
  `domain/signal_selection.py` (`Signal`, `technical_signals`/`fundamental_signals` extractors,
  `select_top_signals` — ranks by `|score−50|·pillar_weight`, then prefers a not-yet-used pillar within
  a `slack`, capped at `max_top_signals`; unknown pillars weight to zero; no `"Data Limited"` padding).
  `score_candidate` builds the signal list from the technical+fundamental sub-scores it already computes
  and stores names on `ScoreBreakdown.top_signals`; `decide` **appends** `analyst.signal.<name>` to the
  recommendation `evidence_refs` (additive → no rationale re-pin). Two tunables
  (`signal_diversity_slack` 5.0, `max_top_signals` 5). **Explanatory only — no score/confidence change,
  no contract change** (analyst 0.1.0). 581 tests (8 new), floor 100.00. Follow-up: add `"sentiment"` to
  the weights map when S37 lands.
- **Sprint 35 — Analyst: fundamental scoring** (P11 cont.). New `domain/fundamental_rules.py`
  (`score_fundamental` — an 8-metric named rule table: P/E, ROE, net margin, current ratio, P/B,
  debt/equity, EPS growth, revenue growth; first-present fallback keys, `require_positive` skips
  ≤ 0, missing keys skipped, average of present sub-scores, `(None, {})` when none usable; ported
  verbatim from the reference bands). `score_candidate` gained a `fundamentals` arg and blends: the
  composite is the technical score alone when no pillar, else the weight-renormalised
  `(0.50·tech + 0.30·fund)/0.80`, and confidence is `floor + composite·span`. New
  `technical_weight`/`fundamental_weight` tunables on `AnalystSettings`. `provider_client` now
  requests the `fundamentals` field; `agent._score` passes per-ticker fundamentals; `recommend`
  populates `Recommendation.fundamental_score` and extends the rationale
  only when present. **No contract change** (0.1.0; `fundamental_score` already existed). **Decision:
  absent fundamentals are skipped, not blended as neutral 50** — composite == technical so every
  existing pinned value was re-used (only a mechanical `fundamentals={}` arg added to call sites).
  Line counts: fundamental_rules 127, scoring 90, recommend 77, settings 76. 573 tests, floor 100.00.
- **Sprint 34 — Provider: fundamentals feed** (P11 cont.). The provider now populates the
  previously-always-empty `MarketData.fundamentals`. New `agents/provider/fundamentals.py`
  (`FinnhubDataSource` — stdlib urllib+json against `/stock/metric?metric=all`; pure `_parse_metrics`
  extracts the 11-key union the analyst reads, coerces float, drops None/bool/non-numeric/missing;
  `_download` pragma-no-cover; fundamentals-only, ohlcv→()) + `agents/provider/composite.py`
  (`CompositeDataSource` routes price/regime → Stooq, fundamentals → Finnhub). `DataSource` port
  gained `fetch_fundamentals`; `FakeDataSource` (fixture + `fail_fundamentals`) / `StooqDataSource`
  (→{}) implement it. `_get_market_data` field-gated on `"fundamentals" in fields`, fetched in a
  separate fault boundary; on fault → empty + `fundamentals_degraded` note + `used_fallback`, OHLCV
  path unaffected. **No contract change** (CONTRACT 0.1.0, owns_graph/external_io untouched), **no
  new dependency**. Existing OHLCV-only callers see `fundamentals == {}` → no re-pin. Line counts:
  fundamentals 96, composite 44, sources 171, agent 138, settings 95 — all < 200. 527 tests, floor
  100.00. Next: analyst fundamental scoring consuming this feed.
- **Sprint 33 — Analyst: patterns, smoothing & calendar** (P11 cont.). Three pure-Python signals
  closing the deterministic technical engine: `domain/indicators_kernel.py` (Nadaraya-Watson
  Gaussian deviation; always-emit Monday `turnaround_signal` — `None` only below 3 bars) +
  `domain/indicators_pattern.py` (swing points → double top/bottom, (inverse) head-and-shoulders,
  ascending/descending triangles) + `domain/technical_rules_pattern.py` (NW ±1.0 → 70/30/50;
  pattern 50 ± conf·30; turnaround 75/50). `score_technical` now also extracts `dates` and
  concatenates the pattern group → composite up to **15** indicators. **No contract/scoring
  change.** `settings.py` (was at the 200L cap) split: indicator periods + the 4 new pattern
  tunables moved to a `_IndicatorSettings(AgentSettings)` base in `settings_indicators.py` (159L);
  `AnalystSettings` inherits it (no caller change). Re-pinned composites: 220-bar → 14 available
  (12 + NW + turnaround; no pattern on the smooth fixture), 40-bar → 11; turnaround a deterministic
  50 in every existing fixture (none ends on a Monday-below-Friday). Final line counts: kernel 54,
  pattern 129, rules_pattern 78, technical_rules 147 — all < 200. 516 tests, floor 100.00.
- **Sprint 32 — Analyst: volume + event signals** (P11 cont.). `domain/indicators_event.py`
  (OBV vs its SMA signal line; golden cross SMA-50/200; each `None` on short history) +
  `domain/technical_rules_event.py` (OBV 70/35, golden 75/25, RSI-2 80/20/50 — RSI-2 reuses
  `indicators.rsi` at period 2). `score_technical` now also extracts `volumes` and concatenates
  the event group → composite up to 12 indicators. No contract change. Re-pinned composites:
  220-bar → 12 available, 40-bar → 9. **Spec-error caught by coding agent:** the ~4-bar pipeline
  fixtures did NOT fully degrade (RSI-2 needs only 3 closes) → shared thin fixtures trimmed to
  2 bars (full degradation → neutral 0.60, wiring intent preserved); changes confined to analyst
  and test fixtures, no other production code. `settings.py` at 178L (warn band). 479 tests, floor
  100.00.
- **Sprint 31 — Analyst: oscillators + volatility** (P11 cont.). Four pure-Python range-based
  indicators in `domain/indicators_range.py` (ATR, Stochastic %K/%D, Williams %R, Choppiness
  Index — each `None` on short/degenerate history, never raises) + `domain/technical_rules_range.py`
  (0–100 bands; ATR%, Stochastic 5-branch, Williams, Choppiness 38.2/61.8). `score_technical` now
  takes sorted bars (derives closes/highs/lows once) and concatenates range sub-scores with the
  momentum group → up to 9 indicators averaged. No contract change. Re-pinned composites: 220-bar
  → 9 available, 40-bar → 7. `settings.py` at 157L (sanctioned warn band). Downstream pipeline
  fixtures still neutral-degrade unchanged. 461 tests, floor 100.00.
- **Sprint 30 — Analyst: technical scoring core** (P11 begins). Pure-Python (no pandas)
  indicator engine: `domain/indicators.py` (RSI, MACD, Bollinger position, SMA-distance, EMA
  crossover — each returns `None` on short history, never raises), `domain/technical_rules.py`
  (0–100 band rules + `score_technical` averaging only available sub-scores, neutral 50 when
  none). `score_candidate` rewired to the composite (`technical_score = mean_subscore/100`);
  `ScoreBreakdown`/`decide` interface unchanged (no contract change). `lookback_days` 7 → 260;
  old heuristic tunables (momentum/MA/score-scale) removed; indicator periods are justified
  tunables with a `macd_fast<slow`/`ema_short<long` validator. Strict-`<` band boundaries.
  Downstream pipeline tests unaffected (thin ~4-bar fixtures → neutral 0.5 → confidence 0.60,
  still clears the strict-`<` floor). 427 tests, floor 100.00. Oscillators/patterns/fundamental/
  sentiment are later P11 slices (fundamental + sentiment blocked on a provider data feed).
- **Sprint 29 — Curator: predictor registry + promotion gate** (**P10 complete**).
  `promote_predictor` capability: evidence gate (`check_promotion_evidence` — frozen accuracy ≥
  `min_promotion_accuracy`, sample_size ≥ min) → operator approval via `supervisor.flag_for_human`
  bus call (subject `predictor:<id>`) + existing `cli approve` → append-only `PredictorPromotion`
  audit node (`PROMOTES → Predictor`, frozen accuracy/sample-size, approval_ref). Idempotent,
  approval-state-driven (not_found/rejected/pending_approval/promoted/already_promoted);
  graph-authoritative `promotion_status` (advisory/pending_approval/load_bearing) on
  `cli predictors`. Orchestration in `promotion.py` (137L); helpers spilled to `agent_support.py`
  to keep `agent.py` at 191L. Contract 0.2.0 → 0.3.0 (`owns_graph += PredictorPromotion`).
  `test_p10_exit.py`: full chain `PredictorPromotion → Predictor → Dataset → TrainingExample →
  TradeNarrative` **and** no decision-node mutation. Real `cli approve predictor:<id>` proven in
  `surfaces/tests/test_registry_surface.py`. 386 tests, floor 100.00. **P10 exit criterion met.**
- **Sprint 28 — Curator: training trigger** (P10, advisory). `train_predictor` capability:
  `select_dataset` (latest or pinned version) → `train_baseline` (deterministic majority-class
  on the train split, alphabetical tie-break, accuracy on the held-out test split) → advisory
  `Predictor` node (frozen metrics in props, `advisory=True`/`promotion_eligible=False`) with a
  `Predictor -[:TRAINED_ON]-> Dataset` edge. Degraded (no dataset / empty train split) → no
  Predictor written, never raises. Orchestration in `agents/curator/predictor.py` (kept
  `agent.py` at 180L); `surfaces/queries/predictors.py` + `cli predictors`. Contract bumped
  0.1.0 → 0.2.0 (`owns_graph += Predictor`); single-writer meta-test green. `test_p10_training_
  boundary.py` proves training mutates no prior node. 366 tests, floor 100.00. Registry +
  promotion deferred to Sprint 29.
- **Sprint 27 — Curator: dataset assembly** (**P10 begins**). `agents/curator/` full
  implementation: `settings.py`, `dataset_store.py` (`DatasetStore` port + `FakeDatasetStore`),
  `domain/assembly.py` (read-only traversal: `TradeNarrative -[:NARRATES]-> Position`, then
  `CloseDecision -[:CLOSES]-> Position` ancestor for the exit-trigger label), `domain/split.py`
  (deterministic index split over stable key order), `domain/manifest.py` (per-purpose version =
  count of existing `Dataset` nodes + 1), `store.py` (`Dataset -[:CONTAINS]-> TrainingExample`,
  `TrainingExample -[:DERIVED_FROM]-> TradeNarrative`), `agent.py` (`build_dataset` +
  `describe_corpus`, degraded manifest below `min_examples_for_split`, never raises).
  `surfaces/queries/datasets.py` + `cli datasets`; `render_datasets` in `render_extras.py`
  (render.py left at 175L). Curator bound in `bind_paper_loop_agents` (handlers only — out of
  the dispatcher loop). `emits=("dataset_published",)` stays declarative (no runtime event bus).
  `depends_on` left untouched (boundary meta-test requires declared deps to resolve, not be
  exercised). **P10 invariant proven:** `test_p10_boundary.py` — every non-curator node identical
  before/after `build_dataset`. 350 tests, floor 100.00. **P10 begun; not closed (Sprint 28).**
- **Sprint 26 — Observability fault metering** (**P9 complete**). `MeteredFaultSink` wired in
  `surfaces/context.py::_context()` through the bus *and* every bound agent's sink (`active_sink`
  passed to `_bind_pipeline` + `OperatorAgent`), so agent-internal faults — caught by each agent's
  own `fault_boundary(reraise=False)` — now reach `faults_total` instead of bypassing the meter.
  `surfaces/tests/test_p9_exit.py` (81L): one test proves request + fault metric families flow to
  the registry; a second drives a real `analyze` with `fail_ohlcv=True` and asserts
  `faults_total{source_agent="analyst"}` (genuine regression guard — fails on the raw-sink bug).
  `docs/observability.md` "Deployed stack" section added. Also repaired four Sprint 25 commits that
  shipped CI-red (ruff/mypy/detect-secrets, mechanical). 326 tests, floor 100.00. **P9 exit met.**
- **Sprint 25 — Stage command wiring + MarketPack** (**P8 complete**). `cli stage promote`
  wired through operator grammar → supervisor gate → `execution.promote_stage`; `MarketPack`
  Protocol + `MarketPackRegistry` in kernel; `USEquitiesSP500Pack` in `orchestration/packs/`;
  `SurfaceContext` gains `pack_registry` field; `cli packs` surface; `surfaces/queries/packs.py`
  (42L); A0 extraction: `cli_commands_queries.py` (60L), `cli_commands.py` → 150L.
  Stage dispatch tests: `test_stage_dispatch.py` (94L), `test_stage_promote_cli.py` (83L).
  G6 proof: `test_p8_exit.py` (103L) registers `EuropeStocksTestPack` entirely in test scope.
  320 tests, floor 100.00. **P8 exit criterion met.**
- **Sprint 24 — Stage gate machinery** (P8 Part 1). `execution.promote_stage` capability;
  `StageTransition` graph node (execution-owned); evidence gate (min runs, approval_rate,
  critical fault block); two-call confirmation pattern (Flag then FlagResolution);
  immediate demotion; graph-authoritative `stage_status`; `_submit` live-adjacent rejection.
  New modules: `stage_flow.py` (116L), `live_gate.py` (36L), `domain/submit.py` (52L),
  `domain/stage_gate.py` (80L), `domain/stage_metrics.py` (33L), `domain/result.py` (36L).
  FlagResolution key: `resolution:flag:stage_promote:<target>:info`. 309 tests, floor 100.00.
- **Sprint 23 — Researcher agent** (**P7 complete**). `agents/researcher/` full implementation:
  `settings.py` (70L), `domain/evidence.py` (61L), `domain/proposal.py` (80L), `store.py` (43L),
  `agent.py` (132L). Heuristic: `avg_confidence < 0.40` → raise `confidence_floor`; `> 0.70` →
  lower; else zero-change proposal. `Experiment -[:PROPOSES]-> ParamChange` provenance.
  `supervisor.flag_for_human` bus call with `subject_ref="proposal:<id>"`. `cli proposals`
  surface (`surfaces/queries/proposals.py` 53L). A0 render extraction: `render_extras.py` (41L)
  and `render_review.py` (26L); `render.py` → 165L. FlagResolution approval key:
  `resolution:flag:proposal:<id>:info`. Researcher bound in `orchestration/bindings.py`.
  296 tests, floor 100.00. **P7 exit: never-applies invariant proven.**
- **Sprint 22 — MCP tool-binding** (**P1 complete**). `surfaces/mcp_server.py` (121L) +
  `surfaces/mcp_tools.py` (146L). Five tools: `command` (operator.interpret →
  supervisor.dispatch_intent; no auto-confirm — AI assistant calls twice explicitly),
  `status`, `runs`, `incidents`, `explain`. Async/sync bridge via `asyncio.to_thread`;
  `_amain`/`main` marked `# pragma: no cover`. `mcp>=1.0` in dev dep group; mypy per-file
  decorator ignores only. `trading-agents-mcp` script entry in pyproject.toml.
  `uv run python -m surfaces.mcp_server` exits cleanly on stdin close. 277 tests, floor 100.00.
  **P1 exit: both bus backends + Neo4j GraphStore + observability + MCP binding all shipped.**
- **Sprint 21 — Incident view + explain on demand** (**P6 exit**). `FaultView` +
  `open_faults(graph)` (all Fault nodes, newest first); `cli incidents`; `cli explain <pos_id>`
  calls `reporter.narrative` on demand and renders `TradeNarrative.story.summary`. A0 refactor:
  `cmd_narrative` + `cmd_approve` extracted to `cli_commands_extra.py` (75L). `test_p6_exit.py`
  (117L) proves run/inspect/approve/recover/explain. 272 tests, floor 100.00.
  **P6 exit criterion met.** `render.py` at 187L — extract helpers before next render addition.
- **Sprint 20 — Trade narrative display + approve command** (P6). `narratives_for_run` query
  reads `TradeNarrative` nodes by `run_id` prop; `RunNarrative(position_id, ticker, summary)`.
  `approve` flipped to available in capability matrix; `resolve_flag_by_subject` store helper;
  `gate.dispatch_intent` resolves matching human-review flag inline for approve family.
  `cli narrative` + `cli approve` commands. `TypedIntent.model_copy` for auto-confirm.
  Tests split into `test_cli_narrative_approve.py`. 266 tests, floor 100.00.
- **Sprint 19 — GraphStore `list_nodes` + position lifecycle** (P6). `list_nodes(label)` added
  to `GraphStore` Protocol, `InMemoryGraphStore` (extracted to `graph_memory.py`), and
  `Neo4jGraphStore` (helpers split into `graph_cypher.py` + `graph_neo4j_queries.py`). All
  `._nodes` internal access removed from surfaces and supervisor health. `surfaces/cli.py`
  extracted to `cli_commands.py` (cli.py 58L; commands 142L). `surfaces/queries/lifecycle.py`
  (`PositionLifecycle`, `position_lifecycle`, `all_position_lifecycles`);
  `surfaces/queries/flags.py` (`FlagView`, `pending_flags`). `cli position` + `cli flags`.
  258 tests, floor 100.00.
- **Sprint 18 — Surfaces foundation + CLI** (P6 begins). `resolve_flag` append-only fix:
  `_replace_node` deleted; `FlagResolution` node appended with `RESOLVES` edge; `health.py` counts
  open flags by `FlagResolution` absence. `surfaces/queries/` projections (`runs.py` 111L,
  `positions.py` 79L, `health.py` 72L); `surfaces/cli.py` 125L; `surfaces/context.py` 110L;
  `surfaces/render.py` 100L. CLI tests infra-free (InMemoryGraphStore + FakeLLMClient). 251 tests,
  floor 100.00. Known gap: `nodes_by_label` uses `._nodes` — silently empty for Neo4j; fix in S19.
- **Sprint 17 — Supervisor capability gate** (P5 — **exit criterion met**). `dispatch_intent`
  enforces hard-NO → confirmation gate → capability matrix in order; confirmation writes/resolves
  `Flag` nodes; `system_status` queries live graph health; `flag_for_human` writes `Flag` nodes
  idempotently. `gate.py` (58L) holds the routing logic cleanly separate from agent.py (173L).
  P5 exit test: `operator.interpret → supervisor.dispatch_intent` with `CommandAudit` + `Message`
  nodes confirmed; policy-parity test (dashboard == MCP) green.
- **Sprint 16 — Operator agent** (P5 begun). `LLMClient` protocol + `FakeLLMClient` in kernel;
  `AnthropicLLMClient` in `agents/operator/`; `OperatorAgent` with `interpret` (all 10 families,
  confirmation policy hardcoded in grammar) and `explain` (graph evidence + LLM narration);
  `CommandAudit -[:PRODUCED_BY]-> LLMCall` + `CommandAudit -[:RESULTED_IN]-> Intent` provenance;
  `domain/result.py` extracted to hold parsing helpers. `agent.py` 148L. 237 tests, floor 100.
- **Sprint 15 — Scheduler + supervisor message lineage** (P4 — **exit criterion met**).
  `step_check_positions` all-hold fix; `SupervisorAgent` (`record_dispatch_run` writes one
  `Message` node per step, `report_fault` writes `Fault` nodes); `RunScheduler` factory;
  dispatcher tracks steps locally and calls `_finish()` before every return; idle proof test.
  Dispatcher refactored: `run_outcome.py` (stop-reason constants), `lineage.py` (position
  traversal), `narratives.py` (fan-out) extracted to stay ≤ 150 lines. 208 tests, floor 100.
  **P4 exit: daily loop on distributed bus, event-driven, supervisor recording message lineage.**
- **Sprint 14 — Dispatcher** (P4 begun). `Dispatcher` in `orchestration/` binds all 7 agents
  and drives `execute_run(trigger)` through scan→analyze→evaluate→submit→check_positions→report
  in order; graceful stop on fault/empty at each step. `orchestration/bindings.py` separates
  agent binding from routing; `orchestration/steps.py` (160 lines) houses typed step functions.
  CeleryBus fix: `disable_sync_subtasks=not eager` unblocks nested calls in eager mode.
  P4 CeleryBus parity test green. 195 tests, floor 100. Near-limit: `steps.py` (160),
  `tests/helpers.py` (161), `test_dispatcher_unit.py` (167) — warn-band only, split on next touch.
- **Sprint 13 — Reporter agent** (P3 — **exit criterion met**). Read-only graph traversal
  produces `RunSnapshot` (portfolio/signal metrics, headline) and `TradeNarrative` (scan-to-exit
  story per position). `Snapshot -[:SUMMARISES]-> PMRun` and `TradeNarrative -[:NARRATES]->
  Position` written. `agent.py` 88 lines. 185 tests, floor 100.
- **Sprint 12 — Monitor agent** (P3). Opens positions from fills (`PMRun → OrderIntent → Fill`
  traversal), evaluates stop/target/time exit rules (integer PCT_SCALE arithmetic), drives
  `execution.execute_close` on the bus, writes `CloseDecision -[:CLOSES]-> Position` and
  `Fill -[:OPENS]-> Position` lineage. 6-agent pipeline test proves the complete P3 provenance
  chain. `MonitorRun` added to `contracts/monitor.py` `owns_graph`. 171 tests, floor 100.
- **Sprint 11 — Execution agent** (P3). Idempotent `PaperBroker` (dedupes by
  `f"{run_id}:{ticker}:{side}"`), four capabilities, `Fill -[:EXECUTES]-> OrderIntent` lineage.
  No `ExecRun` parent — fills keyed directly by idempotency key. 100% coverage.
- **Sprint 10 — Audit-truth & rigor hardening** (P3). Durable PM rejection evidence (`Rejection`
  nodes + lineage); contract value validators; deep-frozen graph props; matched InMemory/Neo4j
  edge identity (parity test); lazily-installed Neo4j uniqueness constraints; split the tight
  kernel modules; Stooq/MA/tie-break fixes. 144 tests; floor de-pinned 100 → 99.5.
- **Sprint 09 — Portfolio manager** (P3 begun). Sizes + risk-checks recommendations into
  `OrderIntent`s (two provider bus calls, deterministic sizing, explainable rejections, money as
  integer cents); `OrderIntent -[:APPROVES]-> Recommendation` lineage; 4-agent pipeline test green.
  130 tests, floor 100. *Audit-truth follow-ups (persist rejections, contract validators) go to
  the hardening sprint.*
- **Sprint 08 — Observability metrics adapter** (P1). Vendor-neutral `Metrics` protocol
  (`NullMetrics` default + `PrometheusMetrics` private-registry backend, no server); both buses
  instrumented for throughput/latency/outcome; `MeteredFaultSink` for fault-rate by source.
  112 tests, floor 99.75.
- **Sprint 07 — Distributed (Celery) bus** (P1). `CeleryBus` implementing `MessageBus` with
  `InProcessBus`-identical semantics (the four behaviours), tested in eager mode; a
  both-backends parity test proves the P1 bus exit; real-broker round-trip integration-marked.
  108 tests, floor 99.74.
- **Sprint 06 — Analyst agent** (P2 — **slice complete**). `analyze` +
  `explain_recommendation`; two provider bus calls (market data + regime), technical scoring,
  confidence gating by `base_min_confidence`, explainable rejections, and `Recommendation
  -DERIVED_FROM-> Candidate` lineage. The full-slice integration test proves the P2-exit
  chain `Recommendation → Candidate → ScanRun → MarketSnapshot`. 101 tests, floor 99.72.
- **Sprint 05 — Scanner agent** (P2). First agent-to-agent call: `run_scan` +
  `explain_filter` request `get_market_data` from `provider` over the bus (no import),
  deterministic filters/ranking with justified tunables, honest degraded handling, and
  cross-agent provenance (`Candidate → ScanRun → MarketSnapshot`). 87 tests, floor 99.67.
- **Sprint 04 — Provider agent** (P2, first agent). `provider` over the in-process bus:
  `get_market_data` + `get_regime`, `DataSource` port (`FakeDataSource` for the gate,
  keyless `StooqDataSource` network-gated), DI-1 integrity gate + VIX regime classifier
  (justified tunables), append-only provenance to the `GraphStore`, secrets `repr=False`.
  Established the agent-composition pattern; `agents` added to coverage. 79 tests, floor 99.6.
- **Sprint 03 — Neo4j GraphStore** (P1, partial). Kernel `GraphStore` protocol +
  `InMemoryGraphStore` + `Neo4jGraphStore` (fake-driver unit tests; live test skips without
  `NEO4J_TEST_URI`); append-only enforced (no prop overwrite), Cypher-injection guarded.
  Retired the relational adapter + Alembic; boundary map → single-writer-per-label. 67
  tests, floor raised to 99.5.
- **Sprint 02 — Relational persistence adapter** (P1, partial; **superseded by
  [ADR-0001](decisions/0001-neo4j-primary-store.md)** — relational store dropped for
  Neo4j). Domain-pure SQLAlchemy 2.0 `Base` + `PersistenceSettings` + a fault-wrapped
  `Database.session()`, plus an Alembic harness; 64 tests; `.env.example` now tracked.
- **Sprint 01 — Kernel runtime spine** (P1, partial). In-process bus + contract-
  bound `AgentBase` with inbound/outbound payload validation and the fault
  channel wired end-to-end; four behaviours covered (round-trip, inbound
  validation, handler raise, unknown capability). 58 tests, floor 99.1.
- **P0 — Boundary map + foundations.** 12 agent contracts + missions, kernel
  descriptors, config governance, central fault channel, the curator agent,
  self-enforcing guards, CI parity. First private push to GitHub.

---

## Pointers

- Product intent: `docs/PRD.md`
- Structure & rules: `docs/architecture.md`
- Sequenced plan: `docs/build-plan.md`
- Configuration governance: `docs/configuration.md`
- Error handling: `docs/error-handling.md`
- Observability & historical data: `docs/observability.md`
- Per-agent charters: `agents/<name>/mission.md`
- Machine boundaries: `contracts/<name>.py`
