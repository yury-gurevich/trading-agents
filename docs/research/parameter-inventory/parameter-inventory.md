# Parameter inventory — every `tunable()` that shapes the system

**Status:** Reference (auto-extracted snapshot) · **Date:** 2026-06-24 · **133 parameters** across 18 files

> Point-in-time snapshot of every `tunable()` declaration — the complete decision-
> parameter surface in one place. The system has no unified catalogue yet; **CI-1**
> (ADR-0013) will generate this automatically. Until then this is the single view.
> Each tunable carries a mandatory **justification** (why its default was chosen).
> Regenerate with the script at the foot of this file.

## `agents/analyst/settings.py` — 13 (decision-shaping)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `lookback_days` | `260` | 2..512 | days | Indicators need up to ~200 trading days of history (SMA200); a ~260-calendar-day window yields enough daily bars. |
| `min_history_bars` | `2` | 2..60 | bars | At least two closes are required before any indicator is meaningful. |
| `confidence_floor` | `0.3` | 0.0..1.0 | — | Keep weak but valid technical evidence below the provider regime gate. |
| `confidence_span` | `0.6` | 0.0..1.0 | — | Let strong technical evidence clear the default 0.60 regime threshold. |
| `technical_weight` | `0.5` | 0.0..1.0 | — | Reference composite weight for the technical pillar. |
| `fundamental_weight` | `0.3` | 0.0..1.0 | — | Reference composite weight for the fundamental pillar; renormalised over present pillars. |
| `sentiment_weight` | `0.2` | 0.0..1.0 | — | Reference composite weight for the sentiment pillar; renormalised over present pillars. |
| `benchmark_ticker` | `'SPY'` | — | — | Relative-strength benchmark; SPY tracks the scanner's S&P 500 universe. |
| `rs_window` | `20` | 2..120 | bars | Reference relative-strength lookback (~one trading month). |
| `relative_strength_weight` | `0.2` | 0.0..1.0 | — | Reference weight of relative strength within the technical pillar (0.8 technical / 0.2 relative strength). |
| `signal_diversity_slack` | `5.0` | 0.0..50.0 | — | Contribution slack letting a lower-scoring signal from an unused pillar be surfaced ahead of another from a pillar already represented. |
| `max_top_signals` | `5` | 1..20 | — | Maximum explanatory signals surfaced per recommendation rationale. |
| `alpha158_pillar_weight` | `0.0` | 0.0..1.0 | — | Fifth scoring pillar weight for the Alpha158 multi-horizon momentum/volatility composite. Default 0.00 = off; operator enables after 20-day shadow IC comparison against the existing technical pillar shows non-trivial incremental information (target: ΔIC ≥ 0.02 on the held-out window). |

## `agents/analyst/settings_indicators.py` — 21 (decision-shaping)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `rsi_period` | `14` | 2..100 | bars | Wilder's canonical RSI lookback; the technical-analysis standard. |
| `macd_fast` | `12` | 2..100 | bars | Standard MACD fast EMA span from the reference indicator definition. |
| `macd_slow` | `26` | 3..200 | bars | Standard MACD slow EMA span; must exceed the fast span. |
| `macd_signal` | `9` | 2..100 | bars | Standard MACD signal EMA span over the MACD line. |
| `bollinger_window` | `20` | 2..200 | bars | Standard Bollinger-band SMA window from the reference definition. |
| `bollinger_sigma` | `2.0` | 0.5..4.0 | — | Standard two-standard-deviation Bollinger band width. |
| `sma_long_period` | `200` | 20..400 | bars | The 200-day SMA is the conventional long-term trend reference. |
| `ema_short_period` | `20` | 2..200 | bars | Fast EMA leg of the crossover trend signal; must trail the long leg. |
| `ema_long_period` | `50` | 3..400 | bars | Slow EMA leg of the crossover trend signal; the trend baseline. |
| `atr_period` | `14` | 2..100 | bars | Wilder's canonical Average True Range lookback (volatility). |
| `stoch_k_period` | `14` | 2..100 | bars | Standard stochastic %K lookback window. |
| `stoch_d_period` | `3` | 1..20 | bars | Standard stochastic %D smoothing over the %K series. |
| `williams_period` | `14` | 2..100 | bars | Standard Williams %R lookback window. |
| `choppiness_period` | `14` | 2..100 | bars | Standard Choppiness Index lookback window. |
| `obv_signal_period` | `20` | 2..100 | bars | Smoothing window for the OBV signal line the rule compares against. |
| `golden_cross_short_period` | `50` | 2..200 | bars | Fast SMA leg of the 50/200 golden cross; the long leg reuses sma_long. |
| `rsi2_period` | `2` | 2..10 | bars | Connors' short RSI lookback for the mean-reversion oversold signal. |
| `nw_bandwidth` | `8.0` | 0.5..50.0 | — | Gaussian kernel width for the Nadaraya-Watson price smoother. |
| `nw_lookback` | `50` | 10..200 | bars | Window the Nadaraya-Watson kernel estimate is computed over. |
| `pattern_lookback` | `60` | 20..200 | bars | Window the geometric chart-pattern swing search scans. |
| `pattern_min_swing_pct` | `2.0` | 0.5..10.0 | — | Swing significance and pattern matching tolerance, in percent. |

## `agents/provider/settings.py` — 20 (decision-shaping)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `base_min_confidence` | `0.6` | 0.0..1.0 | — | Default downstream confidence floor from the reference policy. |
| `base_stop_loss_pct` | `0.05` | 0.0..0.08 | — | Reference protective stop; bounded below the PRD maximum risk cap. |
| `base_take_profit_pct` | `0.1` | 0.01..1.0 | — | Reference reward target paired with the default stop-loss policy. |
| `base_max_holding_days` | `10` | 1..60 | days | Short tactical holding window used until agent scorecards tune it. |
| `max_daily_move_sigma` | `4.0` | 0.1..20.0 | sigma | Flag daily returns that are extreme relative to the requested window. |
| `max_staleness_days` | `3` | 0..30 | sessions | Market data older than three TRADING SESSIONS is called out as stale; the count excludes weekends + NYSE holidays (DL-10), not calendar days. |
| `vix_risk_on_threshold` | `15.0` | 0.0..100.0 | — | Low-volatility VIX level where risk-on defaults may apply. |
| `vix_risk_off_threshold` | `20.0` | 0.0..100.0 | — | Elevated VIX level where new-risk posture should tighten. |
| `vix_high_threshold` | `25.0` | 0.0..100.0 | — | High-volatility VIX level from the reference regime gate. |
| `vix_extreme_threshold` | `35.0` | 0.0..150.0 | — | Extreme-volatility VIX level from the reference regime gate. |
| `finnhub_timeout` | `10` | 1..60 | seconds | Bound the Finnhub fundamentals HTTPS call so a slow feed cannot hang. |
| `ingest_chunk_size` | `0` | 0..500 | — | Universe sub-batch size for paced ingest; 0 disables chunking (one single-shot batch). Tune against the per-ticker feed's per-minute cap. |
| `ingest_chunk_delay_seconds` | `60.0` | 0.0..600.0 | seconds | Pause between ingest chunks so the aggregate per-minute API call rate stays under the free-tier ceiling (Finnhub ~60/min, 4 calls/ticker). |
| `fmp_timeout` | `15` | 1..60 | seconds | Bound the FMP EOD HTTPS call so a slow feed cannot hang the run. |
| `tiingo_timeout` | `15` | 1..60 | seconds | Bound the Tiingo EOD HTTPS call so a slow feed cannot hang the run. |
| `alpaca_data_timeout` | `15` | 1..60 | seconds | Bound the Alpaca bars HTTPS call so a slow feed cannot hang the run. |
| `alphavantage_timeout` | `25` | 1..60 | seconds | Bound the Alpha Vantage sentiment call so a slow feed cannot hang. |
| `finnhub_news_lookback_days` | `7` | 1..90 | days | Trailing window of company news to fetch; recent headlines only, not the full OHLCV lookback. |
| `max_news_per_ticker` | `20` | 1..100 | — | Cap headlines per ticker so a noisy feed cannot dominate the downstream sentiment pillar. |
| `finnhub_earnings_lookahead_days` | `30` | 1..180 | days | Forward window scanned for each ticker's next earnings date; comfortably covers any scanner earnings-exclusion threshold. |

## `agents/scanner/settings.py` — 9 (decision-shaping)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `lookback_days` | `5` | 2..252 | days | Short deterministic first-slice window; broader scans tune this later. |
| `min_relative_strength` | `0.02` | -1.0..5.0 | — | Require a positive lookback return before deeper analyst work. |
| `min_price` | `5.0` | 0.01..1000.0 | USD | Avoid illiquid penny-price names in the first scanner slice. |
| `min_average_volume` | `500000.0` | 0.0..1000000000.0 | shares | Require enough daily liquidity for later sizing and execution checks. |
| `candidate_cap` | `5` | 1..50 | — | Keep the first vertical slice small and explainable for analyst handoff. |
| `max_beta` | `2.5` | 0.0..10.0 | — | Exclude names whose systematic risk (beta vs the benchmark) is too high. |
| `beta_min_observations` | `3` | 2..252 | observations | Minimum aligned daily returns before the beta-cap is trusted to gate. |
| `earnings_exclusion_days` | `5` | 0..60 | days | Exclude names whose next earnings report lands within this many days of the scan, avoiding event-driven gap risk before the analyst sees them. |
| `bypass_scanner_filter` | `False` | — | — | When on, tickers the filters would drop still flow downstream (tagged bypassed in the verdict) so their outcome can be observed — the DL-09 counterfactual that lets a drop be scored against what actually happened. |

## `agents/portfolio_manager/settings.py` — 8 (decision-shaping)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `starting_cash` | `Decimal('100000.00')` | 0.0..1000000000.0 | USD | Seed the first PM slice with a paper portfolio before execution lands. |
| `max_position_pct` | `Decimal('0.10')` | 0.0..1.0 | — | Cap one new order at ten percent of portfolio value for first-slice risk. |
| `max_positions` | `10` | 1..500 | positions | Keep portfolio concentration bounded before sector caps exist. |
| `cash_buffer_pct` | `Decimal('0.05')` | 0.0..0.95 | — | Hold back cash so sizing does not consume the full paper account. |
| `min_order_quantity` | `1` | 1..1000000 | shares | Execution receives whole-share order intents in this slice. |
| `price_lookback_days` | `7` | 0..14 | days | Ask provider for a short window so latest close survives non-trading days. |
| `min_reward_risk_ratio` | `1.5` | 0.0..10.0 | — | Reject setups whose reward-to-risk ratio (target_pct / stop_pct) is below the reference minimum; protects per-trade expectancy. 0 disables the gate. |
| `max_sector_pct` | `Decimal('0.30')` | 0.0..1.0 | — | Cap total deployment into any one sector as a fraction of portfolio value to bound concentration risk; 1.0 disables the gate. |

## `agents/monitor/settings.py` — 4 (decision-shaping)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `default_horizon_days` | `14` | 0..365 | days | Paper-stage holding window when no analyst horizon exists in the graph. |
| `price_lookback_days` | `2` | 0..14 | days | Small rolling window to get the latest close across non-trading days. |
| `default_stop_pct` | `0.05` | 0.0..1.0 | — | Fallback stop policy if OrderIntent lineage is missing stop_pct. |
| `default_target_pct` | `0.1` | 0.0..1.0 | — | Fallback target policy if OrderIntent lineage is missing target_pct. |

## `agents/forecaster/settings.py` — 11 (decision-shaping)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `news_lookback_days` | `7` | 1..90 | days | Recent-headline window scored for a subject's shadow sentiment. |
| `headlines_for_full_confidence` | `5` | 1..50 | headlines | Headline count at which the advisory reading reaches full confidence. |
| `price_lookback_days` | `90` | 30..365 | days | Trailing calendar window of daily bars fetched to build price features. |
| `return_short_horizon` | `1` | 1..10 | days | Short trailing-return horizon in the price feature row. |
| `return_mid_horizon` | `5` | 2..30 | days | Medium trailing-return horizon in the price feature row. |
| `return_long_horizon` | `20` | 5..120 | days | Long trailing-return horizon in the price feature row. |
| `volatility_window` | `20` | 2..120 | days | Window for realized volatility of daily returns. |
| `momentum_window` | `20` | 2..120 | days | Window for the price/SMA momentum and the volume ratio. |
| `bars_for_full_confidence` | `60` | 1..365 | bars | Bar count at which the price reading reaches full confidence. |
| `return_squash_scale` | `0.05` | 0.001..1.0 | return | Logistic scale mapping a predicted return onto the 0-1 value. |
| `system_prompt` | `''` | — | — | Champion slot for the DSPy-compiled macro-event extraction prompt (ADR-0010). Pre-declared for P13; empty until the LLM path ships. |

## `agents/execution/settings.py` — 6 (decision-shaping)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `slippage_bps` | `0` | 0..1000 | bps | Paper fills default to the submitted reference price for deterministic tests. |
| `close_quantity` | `1` | 1..1000000 | shares | CloseDecision names a position but not its quantity until monitor owns position state; use one whole-share close fixtures for this slice. |
| `close_reference_price` | `Decimal('1.00')` | 0.01..1000000.0 | USD | execute_close is fixture-driven before monitor supplies prices; this keeps the broker path exercised without external data. |
| `min_promotion_runs` | `10` | 3..200 | runs | Require ten completed runs before stage promotion. |
| `min_approval_rate` | `0.7` | 0.0..1.0 | — | Minimum approval-rate evidence before stage promotion. |
| `alpaca_timeout` | `15` | 1..60 | seconds | Bound the Alpaca REST call so a slow broker cannot hang the run. |

## `agents/curator/settings.py` — 5 (decision-shaping)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `max_examples` | `5000` | 1..100000 | examples | Cap a single dataset build so out-of-band work never starves trading. |
| `min_examples_for_split` | `3` | 3..1000 | examples | Below this, a 3-way split cannot fill each split; build is degraded. |
| `min_train_examples` | `2` | 1..10000 | examples | Below this the train split cannot establish a majority class; training degrades. |
| `min_promotion_accuracy` | `0.55` | 0.0..1.0 | — | Frozen-evidence floor: a predictor below this accuracy is not promotable. |
| `min_promotion_sample_size` | `5` | 1..100000 | examples | Minimum test-split size behind the accuracy figure to trust it. |

## `agents/researcher/settings.py` — 8 (decision-shaping)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `lookback_days` | `90` | 30..365 | days | Quarterly history for slow changes. |
| `min_sample_runs` | `5` | 3..100 | runs | Multiple runs avoid one-day drift. |
| `min_evidence_window_days` | `30` | 7..365 | days | Monthly window for parameter-change evidence. |
| `max_changes_per_proposal` | `2` | 1..5 | — | Small proposals stay reviewable and reversible. |
| `confidence_floor_reference` | `0.3` | 0.0..1.0 | — | Analyst confidence-floor baseline without importing analyst. |
| `confidence_step` | `0.05` | 0.01..0.2 | — | Gradual threshold moves keep effects measurable. |
| `confidence_low_water` | `0.4` | 0.0..1.0 | — | Below this average, demand stronger signals. |
| `confidence_high_water` | `0.7` | 0.0..1.0 | — | Above this average, allow more candidates. |

## `agents/operator/settings.py` — 4 (plumbing / infra)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `model` | `'claude-sonnet-4-6'` | — | — | Production default for structured human-command intent parsing. |
| `max_tokens` | `512` | 64..4096 | tokens | Intent parsing needs short structured output; cap controls cost. |
| `explain_max_evidence_nodes` | `20` | 1..100 | nodes | Bound graph evidence included in explanation prompts. |
| `system_prompt` | `''` | — | — | Champion slot for the DSPy-compiled interpret system prompt (ADR-0010). Empty = use the dynamic build_interpret_system() construction; non-empty = DSPy-promoted static override. |

## `agents/reporter/settings.py` — 1 (plumbing / infra)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `max_narrative_length_chars` | `2000` | 200..10000 | chars | P3 narratives are short deterministic summaries; this future-proofs dashboard rendering if a later graph adds more evidence legs. |

## `agents/supervisor/settings.py` — 1 (plumbing / infra)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `max_fault_message_chars` | `500` | 80..2000 | chars | Fault nodes should stay scannable in graph views while keeping enough error text for operator triage. |

## `agents/master/settings.py` — 7 (plumbing / infra)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `handshake_timeout_1_seconds` | `10.0` | 1.0..60.0 | seconds | Seconds before master retries an unacknowledged ACTIVATE. |
| `handshake_max_retries` | `5` | 1..20 | — | Maximum EHLO resend attempts before transitioning to INERT. |
| `handshake_timeout_2_seconds` | `300.0` | 30.0..600.0 | seconds | Total wait (seconds) before an unactivated agent transitions to INERT. |
| `grant_policy_path` | `''` | — | — | Filesystem path to the pack's grant-policy JSON; empty = the substrate ships no grants, so every agent type is unknown until a pack supplies one. |
| `secret_map_path` | `''` | — | — | Filesystem path to the pack's secret-map JSON; empty = the substrate entitles no agent type to any secret until a pack supplies the table. |
| `grant_policy_b64` | `''` | — | — | Base64-encoded grant-policy JSON injected at deploy time (cloud); takes precedence over grant_policy_path. Keeps the master image pack-agnostic. |
| `secret_map_b64` | `''` | — | — | Base64-encoded secret-map JSON injected at deploy time (cloud); takes precedence over secret_map_path. Keeps the master image pack-agnostic. |

## `kernel/bus_azure_config.py` — 3 (plumbing / infra)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `connection_string` | `None` | — | — | Primary connection-string credential; set in prod, absent in dev/test. |
| `namespace_endpoint` | `None` | — | — | Managed-identity endpoint; used when connection_string is absent in prod. |
| `publish_timeout_seconds` | `10.0` | 1.0..60.0 | seconds | Cap single-message send latency to avoid blocking the agent loop. |

## `kernel/bus_celery_config.py` — 5 (plumbing / infra)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `celery_broker_url` | `'memory://'` | — | — | Default broker keeps local tests infra-free in eager mode. |
| `celery_result_backend` | `'cache+memory://'` | — | — | In-memory result backend is enough for eager tests; override for Redis. |
| `celery_task_always_eager` | `True` | — | — | Default to synchronous local dispatch so the unit gate needs no broker. |
| `celery_task_eager_propagates` | `False` | — | — | Let the bus convert task faults into error envelopes like InProcessBus. |
| `celery_request_timeout_seconds` | `30.0` | 1.0..300.0 | seconds | Bound distributed waits while leaving room for local worker startup lag. |

## `kernel/graph_neo4j_config.py` — 5 (plumbing / infra)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `neo4j_uri` | `'bolt://localhost:7687'` | — | — | Default local Neo4j graph endpoint. |
| `neo4j_user` | `'neo4j'` | — | — | Conventional local bootstrap user keeps setup predictable. |
| `neo4j_password` | `''` | — | — | Provided out-of-band; empty supports unauthenticated tests. |
| `neo4j_database` | `'neo4j'` | — | — | Target database name. Aura/Community expose only 'neo4j'; a local Desktop/Enterprise instance may use a named db (e.g. trading-agent). |
| `neo4j_connection_timeout_seconds` | `30.0` | 1.0..120.0 | seconds | Fail a broken graph connection promptly while allowing local startup lag. |

## `kernel/metrics_prometheus.py` — 2 (plumbing / infra)

| Param | Default | Range | Unit | Why |
| --- | --- | --- | --- | --- |
| `prometheus_namespace` | `'trading_agents'` | — | — | Keep this app's Prometheus series distinct from host/runtime metrics. |
| `prometheus_subsystem` | `'kernel'` | — | — | This sprint emits from kernel plumbing rather than agent domains. |

## Total: 133 tunable parameters

## Regenerate

Auto-extracted from `agents/**/settings*.py` + `kernel/*_config.py` by walking the
AST for `tunable()` calls. Re-run the generator in the session that produced this, or
rebuild via CI-1's `describe_all()` once it ships (ADR-0013 / S90).
