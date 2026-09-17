# Portfolio Manager — Test plan (living)

Each row pins one law-ID to a **functional test** that proves it. This document is the
**master**: discovering a needed test with no law → add the law to `laws.md` first,
then add a row here. A test's docstring **must cite the law-ID** it proves (conventions §7).

Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID)

**Precondition:** `DEP-BUS, DEP-POSTGRES` must be green first (see `docs/laws/dependencies.md`).

## Inputs / triggers

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-IN-01 | Valid RecommendationSet accepted; all recommendations processed. | happy | `test_portfolio_manager_agent.py::test_evaluate_orders_sizes_order_and_stores_money_as_cents` | 🟩 |
| PM-IN-02 | analysis.recommendations.ready claim-check resolved before evaluate_orders. | pub/sub | `test_pm_pubsub.py::test_recommendations_ready_triggers_orders_ready` | 🟩 |
| PM-IN-03 | Empty RecommendationSet → empty OrderIntentSet with reason "no_recommendations". | boundary | _tbd_ | ⬜ |
| PM-IN-04 | explain_decision returns Explanation; no provider call, no graph write. | read-only | `test_portfolio_manager_agent.py::test_explain_decision_returns_grounded_explanation` | 🟩 |
| PM-TRG-01 | RPC evaluate_orders returns an OrderIntentSet to the caller. | happy | `test_portfolio_manager_agent.py::test_evaluate_orders_sizes_order_and_stores_money_as_cents` | 🟩 |
| PM-TRG-02 | analysis.recommendations.ready → evaluate_orders → portfolio.orders.ready emitted. | pub/sub | `test_pm_pubsub.py::test_recommendations_ready_triggers_orders_ready` | 🟩 |
| PM-TRG-03 | Idle → zero provider calls, zero graph writes. | negative | _tbd_ | ⬜ |

## Outputs

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-OUT-01 | OrderIntentSet always returned; every recommendation accounted for. | happy | `test_portfolio_manager_agent.py::test_evaluate_orders_sizes_order_and_stores_money_as_cents` | 🟩 |
| PM-OUT-02 | OrderIntent has quantity ≥ 1, est_price (Decimal), stop_pct, target_pct, pm_run_id. | schema | `test_portfolio_manager_agent.py::test_evaluate_orders_sizes_order_and_stores_money_as_cents` | 🟩 |
| PM-OUT-03 | RejectedOrder carries a reason string naming the blocking gate. | schema | `test_portfolio_manager_agent.py::test_risk_rejects_when_position_limit_binds` | 🟩 |
| PM-OUT-03 | RejectedOrder gate_report names evaluated secondary failed gates without moving the primary rejection reason. | regression | `test_rejection_gate_reports.py::test_2026_08_07_max_positions_rejection_keeps_cash_gate_failure` | 🟩 |
| PM-OUT-04 | Provider unavailable → all rejected with "provider_degraded" + fault recorded. | degraded | `test_portfolio_manager_agent.py::test_degraded_provider_rejects_honestly_and_records_fault` | 🟩 |
| PM-OUT-05 | Pub/sub event carries claim-check ref only, not OrderIntentSet payload. | pub/sub | `test_pm_pubsub.py::test_recommendations_ready_triggers_orders_ready` | 🟩 |
| PM-OUT-06 | portfolio_state_snapshot captures post-evaluation cash, open positions, and sector weights without a live broker query. | audit | Demoted S156: `test_portfolio_manager_audit.py::test_order_intent_emits_pm_gate_report` proves gate_report emission, not the portfolio_state_snapshot clause. | ⬜ |

## Prohibitions

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-NEV-01 | PM never sends orders to broker; output is OrderIntentSet only. | boundary | `test_portfolio_manager_agent.py::test_explain_decision_returns_grounded_explanation` | 🟩 |
| PM-NEV-02 | PM never calls a data API directly; all prices via provider bus call. | boundary | `test_portfolio_manager_agent.py::test_degraded_provider_rejects_honestly_and_records_fault` | 🟩 |
| PM-NEV-03 | PM never promotes execution stage. | boundary | _tbd_ | ⬜ |
| PM-NEV-04 | Recommendation that fails any risk gate is rejected; no partial bypass. | invariance | `test_portfolio_manager_agent.py::test_risk_rejects_when_position_limit_binds` | 🟩 |
| PM-NEV-05 | quantity is always a whole integer; never fractional. | schema | `test_portfolio_manager_agent.py::test_risk_rejects_when_order_is_below_minimum_quantity` | 🟩 |

## Risk gates

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-NEV-04 | max_sector_pct gate rejects over-concentrated sector orders. | boundary | `test_sector_cap.py::test_rejects_second_same_sector_order_over_cap` | 🟩 |
| PM-NEV-04 | min_reward_risk_ratio rejects low R/R recommendations only when a positive floor is configured; the default floor records without rejection and non-positive stops still reject as invalid. | boundary | `test_reward_risk.py::test_rejects_when_reward_risk_below_minimum`; `test_reward_risk.py::test_rejects_zero_stop_loss_as_undefined`; `test_reward_risk_measured_excursion.py::test_default_reward_risk_floor_is_disclosure_only`; `test_reward_risk_measured_excursion.py::test_low_measured_reward_risk_passes_by_default_as_disclosure`; `test_reward_risk_measured_excursion.py::test_positive_reward_risk_floor_still_rejects_below_floor`; `test_reward_risk_measured_excursion.py::test_reward_risk_floor_is_read_from_the_tunable_value` | 🟩 |
| PM-NEV-04 | max_positions gate rejects when portfolio is full. | boundary | `test_portfolio_manager_agent.py::test_risk_rejects_when_position_limit_binds` | 🟩 |
| PM-NEV-04 | cash_buffer_pct gate rejects insufficient cash orders. | boundary | `test_portfolio_manager_agent.py::test_risk_rejects_when_cash_buffer_binds` | 🟩 |
| PM-NEV-06 | max_names_per_sector cap rejects an over-count same-label name the dollar cap allows. | boundary | `test_sector_name_count.py::test_rejects_third_same_sector_name_over_count_cap` | 🟩 |
| PM-NEV-06 | Already-held same-label names count toward the name cap. | invariance | `test_sector_name_count.py::test_held_position_counts_toward_name_cap` | 🟩 |
| PM-NEV-06 | The cap counts distinct **issuers**, not tickers, in a label whose granularity is whatever the source returns. | boundary | `test_issuer_concentration.py::test_dual_class_order_counts_existing_issuer_exposure` | 🟩 |
| PM-NEV-06 | max_sector_pct reports and compares sector exposure against deployed capital, while preserved replay values remain below the unchanged cap. | boundary | `test_concentration_deployed_sector.py::test_sector_gate_uses_deployed_book_denominator`; `test_concentration_no_shock.py::test_recorded_sector_verdicts_stay_passed_after_denominator_swap` | 🟩 |
| PM-NEV-07 | Two share classes of one issuer count as one name and one exposure across every concentration gate. | invariance | `test_issuer_concentration.py::test_dual_class_order_counts_existing_issuer_exposure` | 🟩 |
| PM-NEV-07 | A ticker absent from the issuer map is its own issuer, and that is a pass, not a not-evaluated outcome. | boundary | `test_issuer_concentration.py::test_absent_issuer_map_entry_is_own_issuer_pass` | 🟩 |
| PM-NEV-08 | An order that would push a correlated cluster above max_correlated_cluster_pct is rejected. | boundary | `test_correlation_concentration.py::test_correlated_cluster_rejects_cross_label_order` | 🟩 |
| PM-NEV-08 | Cluster correlation is computed from bars the run already carries; no provider call is made for it. | boundary | `test_correlation_market_context.py::test_correlation_uses_graph_market_data_without_widening_provider_call` | 🟩 |
| PM-NEV-08 | correlated_cluster_pct reports and compares cluster exposure against deployed capital, while preserved replay values remain below the unchanged cap. | boundary | `test_concentration_deployed_correlation.py::test_cluster_gate_uses_deployed_book_denominator`; `test_concentration_no_shock.py::test_recorded_cluster_verdicts_stay_passed_after_denominator_swap` | 🟩 |
| PM-NEV-09 | A missing sector label yields an explicit not-evaluated outcome, never an empty tuple read as a pass. | negative | `test_issuer_concentration.py::test_missing_sector_label_is_not_evaluated` | 🟩 |
| PM-NEV-09 | Fewer than min_correlation_bars overlapping bars leaves the whole gate not-evaluated when no usable pair remains, never a pass. | negative | `test_correlation_concentration.py::test_every_pair_unusable_still_reports_not_evaluated` | 🟩 |
| PM-NEV-09 | Deployment below the derived floor yields explicit not-evaluated concentration evidence, never a failed zero-denominator contradiction or a hard-coded floor. | negative | `test_concentration_deployed_sector.py::test_below_derived_sector_floor_is_not_evaluated`; `test_concentration_deployed_sector.py::test_floor_is_derived_from_live_tunables`; `test_concentration_deployed_sector.py::test_zero_denominator_helper_does_not_emit_failed_zero_value` | 🟩 |
| PM-NEV-09 | The current deployed book is above the derived sector and correlation floors, so both gates still evaluate normally. | boundary | `test_concentration_deployed_correlation.py::test_current_book_is_above_the_derived_floors` | 🟩 |
| PM-STA-03 | Position cap enforced across all candidates within one run. | gate | `test_portfolio_manager_agent.py::test_risk_rejects_when_position_limit_binds` | 🟩 |

## State & effects

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-STA-01 | PortfolioState is in-process; reconstructable from graph on restart. | stateful | _tbd_ | ⬜ |
| PM-STA-02 | evaluate_orders writes PMRun + OrderIntent/Rejection nodes; append-only. | append-only | `test_pm_pubsub.py::test_order_intent_result_node_in_graph` | 🟩 |

## Determinism & idempotency

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-IDM-01 | Same inputs + same starting portfolio state → same OrderIntentSet. | determinism | `test_scaled_stop_rr_gate.py::test_reward_risk_verdict_is_mode_invariant_when_both_values_scale` | 🟩 |
| PM-IDM-02 | run_id threaded from RecommendationSet to portfolio.orders.ready event. | provenance | `test_pm_pubsub.py::test_run_id_propagated_in_orders_ready_event` | 🟩 |

## Failure & recovery

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-FAIL-01 | Provider unavailable → all rejected + fault; no exception to caller. | fault | `test_portfolio_manager_agent.py::test_degraded_provider_rejects_honestly_and_records_fault` | 🟩 |
| PM-FAIL-02 | Per-recommendation evaluation error → that one rejected; others proceed. | partial | _tbd_ | ⬜ |

## Type alignment

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-TYP-01 | est_price is Decimal, never float. | schema | `test_portfolio_manager_agent.py::test_evaluate_orders_sizes_order_and_stores_money_as_cents` | 🟩 |
| PM-TYP-02 | quantity ≥ 1; stop_pct < target_pct when both present. | schema | `test_portfolio_manager_agent.py::test_evaluate_orders_sizes_order_and_stores_money_as_cents` | 🟩 |
| PM-TYP-03 | OrderIntentSet deserialises from graph node per contract schema. | schema | `test_pm_pubsub.py::test_order_intent_result_is_deserializable` | 🟩 |
| PM-TYP-03 | Each payload carries every field its clauses require, and GateOutcome expresses passed, failed and not-evaluated as three distinct values; CONTRACT.version is authoritative; gate_report is additive and defaults empty for older payloads. | schema | `tests/test_contract_values.py::test_gate_outcome_has_three_wire_states_and_legacy_passed_view`; `tests/test_contract_values.py::test_order_intent_gate_report_is_additive_and_round_trips`; `test_pm_pubsub.py::test_order_intent_result_is_deserializable` | 🟩 |
| PM-TYP-03 | Historical RejectedOrder JSON without gate_report deserializes with an empty report, while current payloads round-trip populated gate_report. | schema | `tests/test_rejected_order_contract.py::test_rejected_order_gate_report_is_additive_for_historical_payloads` | 🟩 |

## Security

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-SEC-02 | Unauthorized caller is refused by the capability gate. | authz | _tbd_ | ⬜ |

## Observability

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-OBS-01 | PMRun node contains all gate outcomes and portfolio snapshot. | audit | Demoted S169-sweep: the cited test asserts a pub/sub `OrderIntentResult` node exists with an `orders` key - weaker than the two sibling PM-OBS-01 rows S156 already demoted for the same clause. 🚨 `portfolio_state_snapshot` exists **nowhere in the codebase** and `OrderIntentSet` has no snapshot field, so this half of the clause is false, not merely untested (DRIFT-039). | ⬜ |
| PM-OBS-01 | PMRun reconstructs recommendations, gate outcomes, reasons, estimated prices, final intents, and pre/post portfolio snapshots. | audit | Demoted S156: `test_portfolio_manager_agent.py::test_evaluate_orders_sizes_order_and_stores_money_as_cents` proves OrderIntent money/gate_report storage only, not full PMRun reconstructability. | ⬜ |
| PM-OBS-01 | Rejection nodes persist rejected-path gate_report evidence for graph reconstruction. | audit | `test_rejection_store.py::test_store_writes_queryable_rejection_gate_report` | 🟩 |
| PM-OBS-02 | Faults routed to central channel; every rejection has a reason. | observable | `test_portfolio_manager_agent.py::test_degraded_provider_rejects_honestly_and_records_fault` | 🟩 |
| PM-OBS-03 | An evaluated cluster gate names the issuers examined, the ones that correlated, and the near misses. | audit | `test_correlation_census.py::test_census_names_the_issuers_it_examined_and_the_ones_it_ruled_out` | 🟩 |
| PM-OBS-03 | A census over zero held issuers renders differently from one that examined and found nothing. | negative | `test_correlation_census.py::test_a_census_of_nothing_says_so_rather_than_rendering_as_a_clean_pass` | 🟩 |
| PM-OBS-03 | The census reaches the gate_report detail the deliberator reads, not just the domain object. | audit | `test_correlation_census.py::test_gate_detail_carries_the_census_beside_the_cluster` | 🟩 |
| PM-OBS-03 | Pairwise skipped correlation comparisons name the issuer and observed overlap in the same census detail. | audit | `test_correlation_census.py::test_skipped_pair_names_the_issuer_and_its_overlap` | 🟩 |
| PM-OBS-04 | Evaluated PM gates disclose whether the opposite verdict was reachable: structurally fixed stop/target comparisons name the base percentages and applied mode; data-varying gates are not labelled structurally fixed; pairwise correlation skips do not disable usable comparisons and no usable pair remains not-evaluated. | audit | `test_reward_risk.py::test_a_structurally_fixed_gate_discloses_that_it_could_not_differ`; `test_correlation_concentration.py::test_one_unusable_pair_does_not_disable_the_whole_gate`; `test_correlation_concentration.py::test_every_pair_unusable_still_reports_not_evaluated`; `test_gate_reachability.py::test_a_gate_whose_value_varies_is_not_marked_structurally_fixed`; `test_correlation_census.py::test_skipped_pair_names_the_issuer_and_its_overlap` | 🟩 |
| PM-OBS-05 | reward_risk varies across measured favourable-excursion profiles instead of collapsing to the old constant ratio. | audit | `test_reward_risk_measured_excursion.py::test_reward_risk_varies_across_measured_excursion_profiles` | 🟩 |
| PM-OBS-05 | measured upside below a positive configured fraction of stop risk is visible and rejectable, while the default is disclosure-only. | boundary | `test_reward_risk_measured_excursion.py::test_low_measured_reward_risk_passes_by_default_as_disclosure`; `test_reward_risk_measured_excursion.py::test_positive_reward_risk_floor_still_rejects_below_floor` | 🟩 |
| PM-OBS-05 | measured reward-risk detail names the target basis and sample inputs and is not labelled structurally fixed under a positive floor. | audit | `test_reward_risk_measured_excursion.py::test_positive_reward_risk_floor_is_informative_not_structural` | 🟩 |

## S204 row declarations

| Law | What the row declares | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-IDN-01 | Recommendation-to-order purpose, portfolio-state gates, and negative authorities need one boundary proof. | boundary | _tbd_ | ⬜ |
| PM-IDN-02 | Exclusive ownership of PMRun, OrderIntent, Rejection, and OrderIntentResult labels needs a single-writer proof. | boundary | _tbd_ | ⬜ |
| PM-STA-04 | OrderIntentResult must capture the final portfolio_state_snapshot; this is unbuilt with the same missing-snapshot finding as DRIFT-039. | audit | _tbd_ | ⬜ |
| PM-ORD-01 | Recommendation iteration order must deterministically affect position and sector caps. | ordering | _tbd_ | ⬜ |
| PM-ORD-02 | Concurrent evaluate_orders requests are unsafe by design and need an explicit single-thread/single-tenant guard or proof. | concurrency | _tbd_ | ⬜ |
| PM-FAIL-03 | Graph write failure must fault, return the computed set, and be safe to retry append-only. | fault | _tbd_ | ⬜ |
| PM-PERF-01 | PM latency budget needs an explicit provider-round-trip/per-candidate bound proof. | performance | _tbd_ | ⬜ |
| PM-SEC-01 | PM must hold no credentials, make no external API calls, and have no direct broker authority. | security | _tbd_ | ⬜ |
| PM-SEC-03 | Removing the analysis.recommendations.ready subscription must quarantine PM without corrupting persisted state. | quarantine | _tbd_ | ⬜ |
| PM-DEP-01 | PM bus dependency stands on the Layer-0 bus charter for request/reply and subscribe/publish. | structural | dependencies.md DEP-BUS-* + probes/checks.py | 🧱 |
| PM-DEP-02 | PM graph dependency stands on the Layer-0 Postgres charter for append-write and claim-check read. | structural | dependencies.md DEP-POSTGRES-* + probes/checks.py | 🧱 |
| PM-DEP-03 | PM provider-feed dependency stands on the Layer-0 feed charter through provider price/regime capabilities. | structural | dependencies.md DEP-FEED-* + probes/checks.py | 🧱 |
