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
| PM-OUT-04 | Provider unavailable → all rejected with "provider_degraded" + fault recorded. | degraded | `test_portfolio_manager_agent.py::test_degraded_provider_rejects_honestly_and_records_fault` | 🟩 |
| PM-OUT-05 | Pub/sub event carries claim-check ref only, not OrderIntentSet payload. | pub/sub | `test_pm_pubsub.py::test_recommendations_ready_triggers_orders_ready` | 🟩 |
| PM-OUT-06 | Approved OrderIntent carries additive gate_report outcomes. | audit | `test_portfolio_manager_audit.py::test_order_intent_emits_pm_gate_report` | 🟩 |

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
| PM-NEV-04 | min_reward_risk_ratio gate rejects low R/R recommendations. | boundary | `test_reward_risk.py::test_rejects_when_reward_risk_below_minimum` | 🟩 |
| PM-NEV-04 | max_positions gate rejects when portfolio is full. | boundary | `test_portfolio_manager_agent.py::test_risk_rejects_when_position_limit_binds` | 🟩 |
| PM-NEV-04 | cash_buffer_pct gate rejects insufficient cash orders. | boundary | `test_portfolio_manager_agent.py::test_risk_rejects_when_cash_buffer_binds` | 🟩 |
| PM-NEV-06 | max_names_per_sector cap rejects an over-count correlated name the dollar cap allows. | boundary | `test_sector_name_count.py::test_rejects_third_same_sector_name_over_count_cap` | 🟩 |
| PM-NEV-06 | Already-held same-sector names count toward the name cap. | invariance | `test_sector_name_count.py::test_held_position_counts_toward_name_cap` | 🟩 |
| PM-STA-03 | Position cap enforced across all candidates within one run. | gate | `test_portfolio_manager_agent.py::test_risk_rejects_when_position_limit_binds` | 🟩 |

## State & effects

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-STA-01 | PortfolioState is in-process; reconstructable from graph on restart. | stateful | _tbd_ | ⬜ |
| PM-STA-02 | evaluate_orders writes PMRun + OrderIntent/Rejection nodes; append-only. | append-only | `test_pm_pubsub.py::test_order_intent_result_node_in_graph` | 🟩 |

## Determinism & idempotency

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-IDM-01 | Same inputs + same starting portfolio state → same OrderIntentSet. | determinism | _tbd_ | ⬜ |
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
| PM-TYP-03 | GateOutcome is additive and round-trips through OrderIntent. | schema | `tests/test_contract_values.py::test_order_intent_gate_report_is_additive_and_round_trips` | 🟩 |

## Security

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-SEC-02 | Unauthorized caller is refused by the capability gate. | authz | _tbd_ | ⬜ |

## Observability

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| PM-OBS-01 | PMRun node contains all gate outcomes and portfolio snapshot. | audit | `test_pm_pubsub.py::test_order_intent_result_node_in_graph` | 🟩 |
| PM-OBS-01 | OrderIntent graph node preserves the serialized gate_report. | audit | `test_portfolio_manager_agent.py::test_evaluate_orders_sizes_order_and_stores_money_as_cents` | 🟩 |
| PM-OBS-02 | Faults routed to central channel; every rejection has a reason. | observable | `test_portfolio_manager_agent.py::test_degraded_provider_rejects_honestly_and_records_fault` | 🟩 |
