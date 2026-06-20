# Monitor — Law Test Plan

| Clause | Status | Test |
| --- | --- | --- |
| MON-IDN-01 | ⬜ | — |
| MON-IDN-02 | ⬜ | — |
| MON-IN-01 | 🟩 | `test_check_positions_opens_position_idempotently`, `test_check_positions_without_fills_returns_empty_result` |
| MON-IN-02 | 🟩 | `test_explain_hold_returns_non_empty_explanation`, `test_explain_hold_without_position_returns_explanation` |
| MON-IN-03 | 🟩 | `test_fills_ready_triggers_decisions_ready` |
| MON-TRG-01 | 🟩 | `test_check_positions_opens_position_idempotently` |
| MON-TRG-02 | 🟩 | `test_fills_ready_triggers_decisions_ready` |
| MON-TRG-03 | 🟩 | `test_explain_hold_returns_non_empty_explanation` |
| MON-TRG-04 | ⬜ | — |
| MON-OUT-01 | 🟩 | `test_check_positions_opens_position_idempotently` |
| MON-OUT-02 | 🟩 | `test_stop_rule_writes_check_close_and_dispatches_execution`, `test_hold_writes_check_without_close_decision` |
| MON-OUT-03 | 🟩 | `test_stop_rule_writes_check_close_and_dispatches_execution`, `test_target_rule_triggers_close`, `test_time_rule_triggers_close` |
| MON-OUT-04 | ⬜ | — |
| MON-OUT-05 | 🟩 | `test_hold_writes_check_without_close_decision` |
| MON-OUT-06 | 🟩 | `test_fills_ready_triggers_decisions_ready` |
| MON-OUT-07 | 🟩 | `test_provider_failure_skips_position_and_records_fault` |
| MON-NEV-01 | 🟩 | `test_stop_rule_writes_check_close_and_dispatches_execution` |
| MON-NEV-02 | ⬜ | — |
| MON-NEV-03 | 🟩 | `test_provider_failure_skips_position_and_records_fault`, `test_missing_provider_handler_skips_position_and_records_fault` |
| MON-NEV-04 | 🟩 | `test_missing_current_price_skips_position_and_records_fault` |
| MON-STA-01 | 🟩 | `test_missing_stop_target_uses_fallback_and_records_fault` |
| MON-STA-02 | 🟩 | `test_monitor_decision_result_node_in_graph` |
| MON-IDM-01 | ⬜ | — |
| MON-IDM-02 | 🟩 | `test_check_positions_opens_position_idempotently` |
| MON-IDM-03 | 🟩 | `test_run_id_propagated_in_decisions_ready_event` |
| MON-ORD-01 | ⬜ | — |
| MON-FAIL-01 | 🟩 | `test_provider_failure_skips_position_and_records_fault`, `test_missing_provider_handler_skips_position_and_records_fault` |
| MON-FAIL-02 | 🟩 | `test_missing_current_price_skips_position_and_records_fault` |
| MON-FAIL-03 | 🟩 | `test_missing_stop_target_uses_fallback_and_records_fault` |
| MON-FAIL-04 | ⬜ | — |
| MON-TYP-01 | ⬜ | — |
| MON-TYP-02 | 🟩 | `test_monitor_decision_result_is_deserializable` |
| MON-TYP-03 | ⬜ | — |
| MON-SEC-01 | ⬜ | — |
| MON-DEP-01 | ⬜ | — |
| MON-DEP-02 | ⬜ | — |
| MON-OBS-01 | 🟩 | `test_monitor_decision_result_node_in_graph` |
| MON-OBS-02 | ⬜ | — |
| MON-PERF-01 | ⬜ | — |
| MON-CAP | ⬜ | — |

**Green: 19 / 40**
