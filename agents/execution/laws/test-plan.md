# Execution — Test plan (living)

Each row pins one law-ID to a **functional test** that proves it. This document is the
**master**: discovering a needed test with no law → add the law to `laws.md` first,
then add a row here. A test's docstring **must cite the law-ID** it proves (conventions §7).

Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID)

**Precondition:** `DEP-BUS, DEP-POSTGRES, DEP-BROKER` must be green first
(see `docs/laws/dependencies.md`).

## Inputs / triggers

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-IN-01 | Valid OrderIntentSet accepted; approved entries are submitted. | happy | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-IN-02 | execute_close accepts a CloseDecisionSet; close entries submitted. | happy | Demoted S156: `test_execution_agent.py::test_execute_close_stage_status_and_reconcile` no longer exists after ADR-0017 retired execute_close. | ⬜ |
| EXEC-IN-03 | portfolio.orders.ready claim-check resolved before submit. | pub/sub | `test_execution_pubsub.py::test_orders_ready_triggers_fills_ready` | 🟩 |
| EXEC-IN-04 | promote_stage confirmed=False is dry-run; no StageTransition written. | boundary | _tbd_ | ⬜ |
| EXEC-TRG-01 | RPC submit returns an ExecutionResult with stage, fills, submitted count. | happy | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-TRG-02 | portfolio.orders.ready → submit → execution.fills.ready emitted. | pub/sub | `test_execution_pubsub.py::test_orders_ready_triggers_fills_ready` | 🟩 |
| EXEC-TRG-03 | RPC execute_close returns ExecutionResult from monitor-sourced closes. | happy | Demoted S156: `test_execution_agent.py::test_execute_close_stage_status_and_reconcile` no longer exists after ADR-0017 retired execute_close. | ⬜ |
| EXEC-TRG-05 | RPC stage_status returns current stage without side effects. | read-only | Demoted S156: `test_execution_agent.py::test_execute_close_stage_status_and_reconcile` no longer exists; no replacement citation adjudicated in this sprint. | ⬜ |
| EXEC-TRG-06 | promote_stage with confirmed=True writes StageTransition. | gate | `test_promote_stage.py::test_promote_stage_confirmed_writes_transition_and_status_reads_graph` | 🟩 |
| EXEC-TRG-07 | Run-start position_sync writes exactly one BrokerPositionSnapshot before downstream scoring is released. | happy | `test_position_sync_work_items.py::test_work_items_prioritize_sync_before_submit`; `test_position_sync_poll.py::test_sync_is_idempotent_per_run` | 🟩 |

## Outputs

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-OUT-01 | ExecutionResult always returned with stage, fills, submitted, pm_run_id. | happy | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-OUT-02 | Fill carries ticker, side, quantity, price (Decimal), broker_order_id, status. | schema | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-OUT-03 | Stage not in {paper, broker_shadow} → submitted=0; no broker call. | gate | `test_promote_stage.py::test_submit_rejects_live_manual_without_broker_call` | 🟩 |
| EXEC-OUT-04 | reconcile returns ReconcileResult with matched count + discrepancies. | reconcile | `test_execution_agent.py::test_reconcile_reports_unrecorded_broker_fill` | 🟩 |
| EXEC-OUT-05 | promote_stage returns PromoteStageResult with from/to stage + evidence. | gate | `test_promote_stage.py::test_promote_stage_writes_flag_when_evidence_passes` | 🟩 |
| EXEC-OUT-06 | execution.fills.ready event is a claim-check ref; run_id in envelope. | pub/sub | `test_execution_pubsub.py::test_run_id_propagated_in_fills_ready_event` | 🟩 |
| EXEC-OUT-07 | A decision unfilled in its session is dropped, recorded via Fill.drop_reason/dropped_at plus an append-only BrokerOrderStatus drop fact, and no raw terminal reason is written into Fill.broker_status. | boundary | _tbd_ | ⬜ |
| EXEC-OUT-08 | Every submitted order records applied and counterfactual tolerance mode, bps and limit price; the counterfactual never reaches the broker. | happy | _tbd_ | ⬜ |
| EXEC-OUT-09 | Every graph-pull ExecutionRun records deliberation posture, deliberation status and posture-blocked buy count as separate facts. | posture | `test_deliberation_posture.py::test_advisory_posture_submits_unvetoed_buy_and_records_warning`; `::test_default_posture_preserves_fail_open_submission_as_advisory`; `::test_deliberation_posture_is_mode_selector_not_tunable`; `test_trading_deliberation_posture.py::test_advisory_fail_open_passes_when_attributed`; `test_graph_vocabulary_deliberation.py::test_execution_run_deliberation_posture_props_are_declared` | 🟩 |

## Prohibitions

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-NEV-01 | Execution has no scoring or selection logic; executes approved intents only. | boundary | `test_execution_agent.py::test_broker_failure_records_rejected_fill_and_fault` | 🟩 |
| EXEC-NEV-02 | Fill.quantity equals OrderIntent.quantity (no override). | invariance | _tbd_ | ⬜ |
| EXEC-NEV-03 | Every broker submission includes a client_order_id; never omitted. | idempotency | `test_execution_agent.py::test_submit_is_idempotent_per_order_intent` | 🟩 |
| EXEC-NEV-04 | promote_stage without evidence gate passes → blocked. | gate | `test_promote_stage.py::test_promote_stage_blocked_without_evidence` | 🟩 |
| EXEC-NEV-05 | Credentials never appear in any response or graph node. | security | _tbd_ | ⬜ |
| EXEC-NEV-06 | Binding posture never opens buy exposure without an arrived DeliberationRun after grace; exits are never delayed or dropped by posture, and arrived vetoes stay honoured. | boundary | `test_deliberation_posture.py::test_binding_posture_blocks_unvetoed_buy_and_records_error`; `::test_binding_posture_does_not_block_sell_only_run`; `::test_arrived_veto_is_honored_identically_under_both_postures` | 🟩 |

## State & effects

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-STA-01 | In-process _recorded dict rebuilt from graph Fill nodes on restart. | stateful | `test_execution_agent.py::test_reconcile_reports_unrecorded_broker_fill` | 🟩 |
| EXEC-STA-02 | Stage is graph-authoritative; latest StageTransition wins. | stateful | `test_stage_gate.py::test_current_stage_from_graph_falls_back_and_reads_latest_transition` | 🟩 |
| EXEC-STA-03 | Graph writes are append-only; no Fill modified after creation. | append-only | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-STA-05 | A Fill with terminal broker_status (filled/rejected) is not re-read and appends no further BrokerOrderStatus; partial still refreshes. | idempotency | `test_fill_refresh_terminal.py::test_filled_broker_status_is_not_reselected_for_order_status_writes`; `::test_rejected_broker_status_is_not_reselected_for_order_status_writes`; `::test_partial_broker_status_still_refreshes_status_evidence`; `test_partial_fill_completion.py::test_partial_broker_status_can_finish_with_final_price` | 🟩 |
| EXEC-STA-06 | An unresolvable realized-PnL conclusion writes Fill.pnl_unresolved_at once and faults once; a marked fill is never re-evaluated. | failure | _tbd_ | ⬜ |

## Determinism & idempotency

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-IDM-01 | Same OrderIntentSet replays identically; broker called once per intent. | idempotency | `test_execution_agent.py::test_submit_is_idempotent_per_order_intent` | 🟩 |
| EXEC-IDM-02 | client_order_id is stable across retries (derived from intent_id). | idempotency | `test_execution_pubsub.py::test_run_id_propagated_in_fills_ready_event` | 🟩 |

## Failure & recovery

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-FAIL-01 | Broker timeout on one order → Fill(rejected) recorded; next order proceeds. | partial | `test_execution_agent.py::test_broker_rejection_records_rejected_fill_and_fault` | 🟩 |
| EXEC-FAIL-02 | Broker total unavailability → all orders rejected; submitted=0; fault. | fault | `test_execution_agent.py::test_broker_failure_records_rejected_fill_and_fault` | 🟩 |
| EXEC-FAIL-03 | Graph write failure → fault recorded; fills already held in-process are safe (idempotency key prevents re-submission to broker); safe to retry — a repeated graph write appends a new record. | fault | `test_graph_write_failure_retry.py::test_graph_write_failure_is_faulted_and_persists_no_fill`; `::test_retry_after_graph_write_failure_never_resubmits_to_the_broker`; `::test_repeated_graph_write_appends_instead_of_overwriting` | 🟩 |

## Type alignment

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-TYP-01 | Fill.price is Decimal; broker string parsed before persisting. | schema | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
| EXEC-TYP-02 | Fill.status ∈ {filled, partial, rejected, pending}; no other values. | schema | `test_execution_agent.py::test_broker_rejection_records_rejected_fill_and_fault` | 🟩 |
| EXEC-TYP-03 | ExecutionResult deserialises from graph node per contract schema. | schema | `test_execution_pubsub.py::test_execution_result_is_deserializable` | 🟩 |

## Security

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-SEC-01 | Credentials never appear in responses, graph nodes, or fault records. | security | _tbd_ | ⬜ |
| EXEC-SEC-03 | Unauthorized caller for submit is refused. | authz | _tbd_ | ⬜ |
| EXEC-SEC-04 | Stage gate blocks live* stage submissions without multi-step promotion. | gate | `test_promote_stage.py::test_submit_rejects_live_manual_without_broker_call` | 🟩 |

## Observability

| Law | What the test must prove | Scenario | Test | Status |
| --- | --- | --- | --- | --- |
| EXEC-OBS-01 | Fill, Reconciliation, and StageTransition nodes reconstructable from graph. | audit | Demoted S169-sweep: the cited `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` proves one `Fill`'s cents and its `Fill`->`OrderIntent` edge only. `Reconciliation` is written in `agents/execution/store.py` and asserted in **no test**; the clause's `ExecutionResultEvent` cross-reference to `pm_run_id`/`intent_id` is asserted nowhere either (`test_execution_pubsub.py::test_execution_result_node_in_graph` checks the label and that a `result` key exists). | ⬜ |
| EXEC-OBS-02 | Broker rejections and stage-gate rejections routed to central channel. | observable | Demoted S169-sweep: the cited test proves the **broker-rejection** third of the clause (rejected `Fill` + 2 faults). Timeouts have no test at all, and no test asserts that a stage-gate rejection reaches the fault channel. | ⬜ |
| EXEC-IDN-03 | BrokerStopOrder, BrokerPositionSnapshot and BrokerOrderStatus are written only by execution. | boundary | `test_broker_evidence_ownership.py::test_broker_evidence_labels_have_execution_only_writers` | 🟩 |
| EXEC-DEP-04 | Graph append-write for the three broker-evidence labels and broker cancel/stop-placement are exercised. | happy | `test_broker_stop_replacement_e2e.py::test_rejected_exit_reprotects_on_later_hold_run` covers `BrokerPositionSnapshot`, `BrokerStopOrder`, broker cancel and stop placement; `test_drop_sweep_append_safe.py::test_2026_07_30_collision_records_drop_without_status_rewrite` covers `BrokerOrderStatus` append-write. | 🟩 |
| EXEC-OBS-03 | Stop placement is an immutable fact, cancellation a cancelled_at marker, broker truth decides liveness, and a held position with no live stop raises UnprotectedPosition and is retried. | failure | `test_broker_stops.py::test_execute_pm_node_places_one_weighted_broker_stop_idempotently`; `test_exit_stop_cancel.py::test_cancellation_is_an_appended_marker_not_a_deletion`; `test_exit_stops.py::test_rejected_exit_leaves_position_loudly_unprotected`; `test_broker_stop_replacement.py::test_cancelled_stop_is_replaced_on_next_run`; `test_broker_stop_replacement_e2e.py::test_rejected_exit_reprotects_on_later_hold_run`; `tests/test_broker_stop_liveness.py::test_filled_sibling_fill_makes_uncancelled_stop_inactive`; `tests/test_broker_stop_liveness.py::test_cancelled_stop_with_nonterminal_fill_stays_inactive`; `tests/test_broker_stop_liveness.py::test_resting_stop_fill_keeps_stop_live`; `tests/test_broker_stop_liveness.py::test_missing_sibling_fill_keeps_stop_live`. | 🟩 |
| EXEC-OBS-04 | Deliberation fail-open severity follows recorded posture, so advisory outages are warnings and binding no-verdict buy submissions are errors that acceptance can distinguish. | observable | `test_deliberation_posture.py::test_advisory_posture_submits_unvetoed_buy_and_records_warning`; `::test_binding_posture_blocks_unvetoed_buy_and_records_error`; `::test_default_posture_preserves_fail_open_submission_as_advisory`; `test_trading_deliberation_posture.py::test_advisory_fail_open_fails_without_reason`; `test_trading_acceptance_deliberation.py::test_advisory_fail_open_deliberation_run_passes_acceptance` | 🟩 |
| EXEC-OBS-05 | Liveness of an execution broker fact is asked in exactly one place; a terminal BrokerStopOrder is not live regardless of cancelled_at; a resting-stop Fill is not an open order; and the sweep compares broker and graph liveness. | observable | `tests/test_broker_stop_liveness.py::test_filled_sibling_fill_makes_uncancelled_stop_inactive`; `tests/test_broker_fill_lifecycle.py::test_resting_stop_fill_is_not_an_open_order_fill`; `tests/test_broker_fill_lifecycle.py::test_pending_buy_fill_is_an_open_order_fill`; `agents/execution/tests/test_drop_sweep_liveness.py::test_sweep_raises_no_mismatch_for_dead_stop_order`; `agents/execution/tests/test_drop_sweep_liveness.py::test_live_stop_mismatch_fault_carries_context`; `tests/test_broker_lifecycle_invariants.py::test_broker_lifecycle_vocabulary_lives_in_one_module` | 🟩 |
