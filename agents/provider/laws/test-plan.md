# Provider — Test plan (living)

Each row pins one law-ID to a **functional test** that proves it across the relevant input/output
space. This document is the **master**: discovering a needed test with no law → add the law to
[`laws.md`](laws.md) first (new ID), then add a row here. A functional test's docstring **cites the
law-ID** it proves (conventions §7).

Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID) · ⛔ blocked (gray dep).

**Precondition:** every row is ⛔ until the provider's dependencies are green —
`DEP-FEED, DEP-POSTGRES, DEP-BUS, DEP-CLOCK, DEP-CONFIG` (see `docs/laws/dependencies.md`).

## Inputs / triggers

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-IN-01 | A valid market-data request is accepted and serves exactly the requested fields. | happy | `test_provider_fundamentals.py::test_fundamentals_populated_when_field_requested` | 🟩 |
| PROV-IN-03 | Empty tickers / bad window / unsupported field → typed rejection, no crash, no empty-success. | boundary ×3 | _tbd_ | ⬜ |
| PROV-IN-04 | A request naming an undeclared endpoint / extra field is refused, not honoured. | adversarial | _tbd_ | ⬜ |
| PROV-IN-05 | Identical request from two different sender roles yields identical handling. | invariance | _tbd_ | ⬜ |
| PROV-TRG-01 | The provider acts only on a recorded data need: a bus request (a subscribed-topic data-request event or an authorised capability request), an unconsumed `RunRequest` on the graph with no bus event, or an `AnalystRun`'s qualifying buys with no `BarrierHistory`; never self-initiated. | pub/sub + capability + graph-pull + barrier + idle | `test_provider_pubsub.py::test_market_data_request_event_triggers_ready_event`; `test_provider_agent.py::test_get_market_data_round_trips_and_writes_provenance`; `test_graph_pull_trigger.py::test_a_recorded_run_request_is_ingested_with_no_bus_event`; `test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch`; `test_graph_pull_trigger.py::test_an_idle_graph_asks_the_feed_for_nothing` | 🟩 |
| PROV-TRG-02 | Never self-triggers: idle (no recorded need) ⇒ zero external calls, zero records however often it polls; a recorded need found unconsumed is a trigger; pending work is found by key and edge alone (`RunRequest` without `INGESTED_BY`, current `AnalystRun` without `BARRIER_HISTORY_BY`) and props are fetched only for those nodes. | negative + graph-pull + payload bound | `test_graph_pull_trigger.py::test_an_idle_graph_asks_the_feed_for_nothing`; `test_graph_pull_trigger.py::test_a_recorded_run_request_is_ingested_with_no_bus_event`; `tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work`; `tests/test_poll_payloads.py::test_the_barrier_backlog_is_never_fetched` | 🟩 |
| PROV-TRG-05 | A `RunRequest`'s ingest serves that run's as-of whenever the provider reaches it: the window ends on the as-of and starts the declared lookback before it (single and chunked path), the lookback is checked against the sessions up to the as-of, the regime is read as of it, news and earnings are anchored on it; an as-of absent, not exactly `YYYY-MM-DD`, or after today (UTC) is refused before any fetch; an ingest with no run serves today (UTC); fundamentals and sectors are not point-in-time. | past as-of × single + chunked + regime + news/earnings + coverage; as-of today; no run; refusals ×9; writer↔reader; sessions counted on NYSE's calendar 2016–2025 (S250 return 1) | `test_run_as_of_window.py::test_a_runs_market_window_ends_on_its_as_of; test_run_as_of_window.py::test_the_regime_is_read_as_of_the_runs_as_of; test_run_as_of_window.py::test_the_chunked_path_serves_the_same_as_of; test_run_as_of_window.py::test_news_and_earnings_are_anchored_on_the_as_of; test_run_as_of_window.py::test_a_run_whose_as_of_is_today_is_unchanged; test_run_as_of_window.py::test_an_ingest_with_no_run_keeps_todays_window; test_run_as_of_refusals.py::test_the_coverage_check_counts_sessions_up_to_the_as_of; test_run_as_of_refusals.py::test_a_lookback_short_of_the_as_ofs_sessions_is_refused; test_run_as_of_refusals.py::test_a_request_with_no_usable_as_of_is_refused_before_any_fetch; orchestration/tests/test_start_as_of.py::test_the_provider_serves_the_as_of_the_dispatcher_wrote; test_market_calendar_history.py::test_each_year_holds_nyses_sessions; tests/test_replay_history_calendar.py::test_every_sessions_declared_window_holds_the_required_bars` | 🟩 |

## Outputs (total space)

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-OUT-01 | Response carries validated facts + quality record + provenance for the requested fields. | happy | `test_provider_agent.py::test_get_market_data_round_trips_and_writes_provenance` | 🟩 |
| PROV-OUT-02 | Regime request → regime context + FMP `^VIX` inputs/freshness + the VIX thresholds its label was selected with + provenance. | happy + below/at/above default and moved thresholds | `test_fmp_vix.py::test_fmp_vix_uses_same_session_bar_as_measured; test_sources.py::test_market_source_routes_regime_to_fmp_vix; test_provider_agent.py::test_get_regime_maps_vix_to_policy_and_graph`; `tests/test_score_arithmetic_regime.py::test_provider_records_the_thresholds_at_every_classification_boundary` | 🟩 |
| PROV-OUT-03a | Clean feed → SUCCESS quality. | success | `test_domain.py::test_integrity_clean_short_window_has_no_notes` | 🟩 |
| PROV-OUT-03b | Stale/missing feed → DEGRADED, flagged, still a valid (non-empty-silent) response. | degraded | `test_provider_agent.py::test_integrity_anomaly_is_reported_without_crashing` | 🟩 |
| PROV-OUT-03c | Boundary failure → typed FAULT, recorded. | fault | `test_provider_agent.py::test_source_failure_records_fault_and_returns_degraded_data` | 🟩 |
| PROV-OUT-03 | Missing/stale regime `^VIX` → warning evidence on a valid response, no incident ref. | degraded | `test_provider_regime_vix.py::test_prior_session_vix_warns_without_regime_incident_ref; test_provider_regime_vix.py::test_missing_vix_warns_and_keeps_regime_usable` | 🟩 |
| PROV-OUT-04 | A served market fact's provenance names one recorded `MarketSnapshot` holding the fetch time (`created_at`) and the fallback flag (`used_fallback`, mirrored as the `market_data_degraded` incident ref); neither the serving source nor a transformation is recorded (work-queue 105). | audit, clean + degraded | `test_served_fact_provenance.py::test_a_served_fact_links_to_its_fetch_time_and_fallback_flag`; `test_provider_agent.py::test_get_market_data_round_trips_and_writes_provenance` | 🟩 |
| PROV-OUT-05 | A second request appends a new record; the prior record is unchanged. | append-only | _tbd_ | ⬜ |
| PROV-OUT-07 | A bar's volume is the consolidated tape's, never one venue's; a request asks only for what the source's entitlement serves; a refusal fails loud per `PROV-FAIL-01`, never an empty success, never a silent one-venue fallback; a bar's prices are raw (the request names no adjustment). | entitlement + default + refusal + raw | `test_alpaca_data.py::test_provider_default_feed_is_the_consolidated_tape; test_alpaca_sip.py::test_sip_request_for_a_window_ending_today_ends_clear_of_the_wall; test_alpaca_request.py::test_sip_past_window_ends_at_the_midnight_after_it; test_alpaca_sip.py::test_iex_request_is_the_query_the_source_always_sent; test_alpaca_sip.py::test_refused_sip_request_raises_and_never_asks_another_feed; orchestration/tests/test_trading_vault_probe_feed.py::test_alpaca_data_probe_tests_the_fleets_feed; test_alpaca_raw_bars.py::test_the_bars_request_asks_for_no_price_adjustment` | 🟩 |

## Prohibitions

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-NEV-01 | A degraded fetch never yields an unflagged "clean" response. | degraded | `test_provider_agent.py::test_integrity_anomaly_is_reported_without_crashing; test_provider_regime_vix.py::test_missing_vix_warns_and_keeps_regime_usable` | 🟩 |
| PROV-NEV-03 | No call is made to any non-declared endpoint (egress assertion). | adversarial | _tbd_ | ⬜ |
| PROV-NEV-04 | No credential appears in any response, log line, or error. | leak-scan | `test_provider_agent.py::test_provider_outputs_do_not_leak_credentials; test_fmp_vix.py::test_fmp_vix_failure_reason_does_not_expose_api_key` | 🟩 |
| PROV-NEV-05 | Boundary meta-test: provider imports no agent; writes only its own labels. | static + runtime | _tbd_ | ⬜ |
| PROV-NEV-06 | An attempt implying overwrite of a prior record does not mutate it. | append-only | _tbd_ | ⬜ |
| PROV-NEV-07 | A missing datum is reported as missing, never filled with a fabricated value. | degraded | `test_sector_source.py::test_parse_sector_missing_empty_or_non_string_yields_none` | 🟩 |
| PROV-NEV-08 | The provider returns raw news headlines and performs no sentiment/score/classification. | boundary | `test_provider_news.py::test_news_populated_when_field_requested` | 🟩 |

## State / idempotency / ordering

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-STA-01 | Cached vs. fresh fetch of the same data produce the same validated result. | invariance | `test_provider_agent.py::test_get_market_data_round_trips_and_writes_provenance` | 🟩 |
| PROV-IDM-01 | Same request and same recorded external inputs produce identical validated facts and quality classification with provenance. | determinism | Demoted S156: `test_domain.py::test_integrity_nonzero_sigma_without_anomaly_stays_clean` proves a non-anomalous sigma path stays clean, not deterministic replay. | ⬜ |
| PROV-IDM-02 | Re-running a request yields a fresh valid record, no corruption/dupe-meaning. | idempotency | _tbd_ | ⬜ |
| PROV-ORD-02 | Two concurrent requests each produce their own correct record. | concurrency | _tbd_ | ⬜ |

## Failure / recovery

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-FAIL-01 | Unreachable/garbled source → degraded/fault, never crash, never bad-as-good. | fault | `test_provider_agent.py::test_source_failure_records_fault_and_returns_degraded_data; test_fmp_vix.py::test_fmp_vix_failures_return_missing_without_raising` | 🟩 |
| PROV-FAIL-02 | Mixed availability → partial response, missing parts flagged per-item. | partial | `test_provider_fundamentals.py::test_fundamentals_failure_notes_without_tainting_ohlcv` | 🟩 |
| PROV-FAIL-03 | After a failed request, a retry succeeds; no corrupt state remained. | recovery | _tbd_ | ⬜ |
| PROV-FAIL-05 | DEP-FEED red ⇒ fail-loud (degraded/fault), no fabrication. | dep-red | _tbd_ | ⬜ |

## Type alignment

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-TYP-01 | Output types equal the consumer contracts' expected types (no drift). | contract | Demoted S156: `test_provider_agent.py::test_get_market_data_round_trips_and_writes_provenance` proves a clean response shape and provenance node, not the full consumer-contract type surface. | ⬜ |
| PROV-TYP-02 | Money/prices are exact (no lossy float); units explicit. | precision | _tbd_ | ⬜ |
| PROV-TYP-03 | Unsupported request shape → typed rejection, not a guess. | boundary | `test_sector_source.py::test_parse_sector_non_dict_or_malformed_yields_none` | 🟩 |

## Security

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-SEC-01 | It holds no authority beyond data-feed creds + its own labels (privilege inventory). | audit | _tbd_ | ⬜ |
| PROV-SEC-02 | Keys are injected, never present in outputs/logs/errors. | leak-scan | `test_provider_agent.py::test_provider_outputs_do_not_leak_credentials; test_fmp_vix.py::test_fmp_vix_failure_reason_does_not_expose_api_key` | 🟩 |
| PROV-SEC-04 | A poisoned/over-broad request cannot cause a trade/order/fund effect (blast-radius). | adversarial | _tbd_ | ⬜ |
| PROV-SEC-05 | A crafted request cannot redirect egress to an arbitrary URL (confused-deputy). | adversarial | _tbd_ | ⬜ |
| PROV-SEC-07 | An unauthorized caller is refused by the capability gate. | authz | `test_provider_reconcile.py::test_unauthorized_caller_is_refused_by_the_capability_gate` | 🟩 |

## Observability / performance

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-OBS-02 | A boundary fault appears on the central fault channel with provenance. | fault | `test_provider_agent.py::test_source_failure_records_fault_and_returns_degraded_data` | 🟩 |
| PROV-OBS-03 | Degradation is queryable from the graph, not buried. | degraded | Demoted S156: `test_provider_fundamentals.py::test_fundamentals_failure_degrades_without_affecting_ohlcv` no longer exists; the live renamed fundamentals test asserts response notes, not queryable graph degradation. | ⬜ |
| PROV-PERF-01 | A hanging source is cut off at the timeout, not waited on indefinitely. | timeout | _tbd_ | ⬜ |

## Historical store & PRD-reconciled clauses (added v0.1)

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-STA-01 | The store durably retains deep history; a later request reads it back without re-fetching. | store | `test_provider_pubsub.py::test_market_data_claim_check_node_is_in_graph` | 🟩 |
| PROV-STA-03 | History is served from the store; the feed is hit only to fill/extend a missing range; stored == fresh for the same as-of. | store | _tbd_ | ⬜ |
| PROV-STA-04 | A stale/missing range is flagged in the quality record; a stale datum is never served as fresh. | freshness | `test_domain.py::test_integrity_rejects_invalid_bars_and_reports_stale_tickers` | 🟩 |
| PROV-IN-06 | A deferred field (FRED/EDGAR) is lawful to request but answered DEGRADED/unavailable until built. | deferred | _tbd_ | ⬜ (deferred, non-blocking) |
| PROV-OUT-02 | A regime response carries the regime-derived policy defaults (stop/target/holding). | happy | `test_provider_agent.py::test_get_regime_maps_vix_to_policy_and_graph` | 🟩 |
| PROV-OUT-06 | A degraded fetch emits `market_data_degraded` consistently with the response's quality record. | degraded | _tbd_ | ⬜ |
| PROV-NEV-08 | The provider returns raw news headlines and performs no sentiment/score/classification. | boundary | `test_provider_news.py::test_news_populated_when_field_requested` | 🟩 |

## S204 row declarations

| Law | What the row declares | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-IDN-01 | Provider's acquire/validate/serve-market-facts purpose needs a boundary proof across price, optional facts, and regime. | boundary | _tbd_ | ⬜ |
| PROV-IDN-02 | Provider as the single data boundary needs a system-wide proof that other agents do not touch market-data APIs. | boundary | _tbd_ | ⬜ |
| PROV-IDN-03 | Provider exclusive ownership of market-fact/regime artifacts and durable store needs a single-writer proof. | boundary | _tbd_ | ⬜ |
| PROV-IN-02 | Regime request with a single as-of date is accepted and served. | happy | _tbd_ | ⬜ |
| PROV-TRG-03 | Invalid requests must be rejected before any fetch occurs. | boundary | _tbd_ | ⬜ |
| PROV-TRG-04 | An `AnalystRun` with a buy carrying both barriers and no `BarrierHistory` triggers the barrier history; sells, holds, a buy missing a barrier, or no recommendation set trigger nothing; the loop carries both work kinds. | trigger | `test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch; test_barrier_history.py::test_a_run_without_a_qualifying_buy_gets_no_history; test_barrier_history.py::test_the_provider_loop_carries_both_work_kinds; tests/test_barrier_current_run.py::test_the_provider_writes_history_for_a_current_run_only; tests/test_barrier_current_run.py::test_the_provider_deployed_work_list_uses_the_wall_clock` | 🟩 |
| PROV-OUT-08 | One OHLCV request through the fetch path (feed and end rule, validation, the `PROV-OUT-09` guard) shared with the daily request, for exactly the qualifying tickers over a window holding `barrier_history_sessions` sessions; one linked `BarrierHistory` with ≤ 760 bars and the count per ticker; dropped tickers named; stale ones marked; a failed fetch still writes a failed node. | happy + partial + fault | `test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch; test_barrier_history_failures.py::test_a_dropped_ticker_carries_its_named_reason; test_newest_session_guard.py::test_a_real_history_day_never_drops_a_buy_from_its_barrier_history; test_barrier_history_failures.py::test_a_failed_fetch_still_writes_a_failed_node; test_barrier_history_failures.py::test_an_exception_in_the_fetch_path_still_writes_a_failed_node; test_barrier_history.py::test_the_history_passes_the_packs_vocabulary_guard; agents/forecaster/tests/test_barrier_route.py::test_a_failed_fetch_never_leaves_the_forecaster_waiting` | 🟩 |
| PROV-OUT-09 | The extreme-move guard judges each ticker's newest bar only, against the pooled moves of every ticker's bar on that same session; beyond `max_daily_move_sigma` σ the ticker is excluded, named in `anomalous_tickers`, a per-ticker partial degradation, never a whole-batch taint; fewer than two moves or no spread is not judged; an older bar is never re-judged; one guard for the daily request and the barrier history; a pool of n moves cannot exceed √(n−1) σ, so it excludes only on a session of more than `max_daily_move_sigma`² + 1 moves. | history day + newest bar + both paths + lagging ticker + abstain + ceiling | `test_newest_session_guard.py::test_a_real_old_extreme_day_keeps_the_name; test_newest_session_guard.py::test_a_bad_newest_bar_is_still_dropped_by_name; test_newest_session_guard.py::test_the_daily_ingest_keeps_a_name_with_a_real_crash_mid_window; test_newest_session_guard.py::test_a_real_history_day_never_drops_a_buy_from_its_barrier_history; test_newest_session_guard.py::test_a_lagging_ticker_is_judged_on_its_own_newest_session; test_newest_session_guard.py::test_a_session_of_one_move_abstains; test_newest_session_guard.py::test_a_session_of_65_names_or_fewer_cannot_pass_8_sigma; test_barrier_history_failures.py::test_a_dropped_ticker_carries_its_named_reason; test_provider_agent.py::test_integrity_anomaly_is_reported_without_crashing` | 🟩 |
| PROV-OUT-03 | Exactly one of SUCCESS, DEGRADED, or FAULT is produced for every request; existing split rows do not prove the total/exclusive space. | total-space | _tbd_ | ⬜ |
| PROV-NEV-02 | Provider must never score, rank, size, order, or decide. | boundary | _tbd_ | ⬜ |
| PROV-STA-02 | Provider side effects are limited to fact/regime appends, degradation events, metrics, and faults. | boundary | _tbd_ | ⬜ |
| PROV-STA-05 | Provider carries no decision state between requests. | state | _tbd_ | ⬜ |
| PROV-ORD-01 | Requests are independent and have no prior-request dependency. | ordering | _tbd_ | ⬜ |
| PROV-ORD-03 | Duplicate or late requests are independently safe. | idempotency | _tbd_ | ⬜ |
| PROV-FAIL-04 | Append-only correction means rollback is neither required nor possible. | recovery | _tbd_ | ⬜ |
| PROV-OBS-01 | Every served fact must be reconstructable from graph provenance plus quality record. | audit | _tbd_ | ⬜ |
| PROV-PERF-02 | N-ticker requests need a stated latency budget and surfaced latency metrics. | performance | _tbd_ | ⬜ |
| PROV-SEC-03 | Provider cannot grant capabilities, widen endpoint set at runtime, or write outside owned labels. | security | _tbd_ | ⬜ |
| PROV-SEC-06 | Provider egress must be restricted to declared market-data endpoints. | security | _tbd_ | ⬜ |
| PROV-SEC-08 | Provider must be independently disableable/quarantinable without corrupting the system. | quarantine | _tbd_ | ⬜ |
| PROV-DEP-01 | Provider feed dependency stands on the Layer-0 feed charter. | structural | dependencies.md DEP-FEED-* + probes/checks.py | 🧱 |
| PROV-DEP-02 | Provider graph dependency stands on the Layer-0 Postgres charter. | structural | dependencies.md DEP-POSTGRES-* + probes/checks.py | 🧱 |
| PROV-DEP-03 | Provider bus dependency stands on the Layer-0 bus charter. | structural | dependencies.md DEP-BUS-* + probes/checks.py | 🧱 |
| PROV-DEP-04 | Provider clock dependency stands on the Layer-0 clock charter for fetch-time/staleness provenance. | structural | dependencies.md DEP-CLOCK-* + probes/checks.py | 🧱 |
| PROV-DEP-05 | Provider config/secrets dependency stands on the Layer-0 config charter. | structural | dependencies.md DEP-CONFIG-* + probes/checks.py | 🧱 |

> Rows are intentionally implementation-agnostic. At **reconciliation**, each `_tbd_` becomes a real
> `agents/provider/tests/…::test_name`; if the code can't satisfy a row, that is a drift finding —
> fix the code, or (if the law is genuinely lacking) amend `laws.md` with a version bump.
