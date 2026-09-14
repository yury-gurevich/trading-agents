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
| PROV-TRG-01 | No output is produced without an inbound request. | negative | `test_provider_pubsub.py::test_market_data_request_event_triggers_ready_event` | 🟩 |
| PROV-TRG-02 | Idle (no request) ⇒ zero external calls, zero records. | negative | _tbd_ | ⬜ |

## Outputs (total space)

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-OUT-01 | Response carries validated facts + quality record + provenance for the requested fields. | happy | `test_provider_agent.py::test_get_market_data_round_trips_and_writes_provenance` | 🟩 |
| PROV-OUT-02 | Regime request → regime context + its inputs + provenance. | happy | `test_domain.py::test_regime_classifier_covers_vix_bands` | 🟩 |
| PROV-OUT-03a | Clean feed → SUCCESS quality. | success | `test_domain.py::test_integrity_clean_short_window_has_no_notes` | 🟩 |
| PROV-OUT-03b | Stale/missing feed → DEGRADED, flagged, still a valid (non-empty-silent) response. | degraded | `test_provider_agent.py::test_integrity_anomaly_is_reported_without_crashing` | 🟩 |
| PROV-OUT-03c | Boundary failure → typed FAULT, recorded. | fault | `test_provider_agent.py::test_source_failure_records_fault_and_returns_degraded_data` | 🟩 |
| PROV-OUT-04 | A served fact's provenance lets you reconstruct source + fetch-time. | audit | Demoted S169-sweep: the cited test proves only that `provenance.graph_node_id` resolves to a `MarketSnapshot`. 🚨 `Provenance` has no source or transformation field and `MarketSnapshot` records `created_at` plus a boolean `used_fallback` - so fetch-time is reconstructable but **which vendor served the fact is not** (DRIFT-040). | ⬜ |
| PROV-OUT-05 | A second request appends a new record; the prior record is unchanged. | append-only | _tbd_ | ⬜ |

## Prohibitions

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PROV-NEV-01 | A degraded fetch never yields an unflagged "clean" response. | degraded | `test_provider_agent.py::test_integrity_anomaly_is_reported_without_crashing` | 🟩 |
| PROV-NEV-03 | No call is made to any non-declared endpoint (egress assertion). | adversarial | _tbd_ | ⬜ |
| PROV-NEV-04 | No credential appears in any response, log line, or error. | leak-scan | `test_provider_agent.py::test_provider_outputs_do_not_leak_credentials` | 🟩 |
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
| PROV-FAIL-01 | Unreachable/garbled source → degraded/fault, never crash, never bad-as-good. | fault | `test_provider_agent.py::test_source_failure_records_fault_and_returns_degraded_data` | 🟩 |
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
| PROV-SEC-02 | Keys are injected, never present in outputs/logs/errors. | leak-scan | `test_provider_agent.py::test_provider_outputs_do_not_leak_credentials` | 🟩 |
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
