# Reporter — Law Test Plan

| Clause | Status | Test |
| --- | --- | --- |
| RPT-IDN-01 | 🟩 | `test_metrics_narrative.py::test_dropped_decision_is_visible_but_not_rejected` |
| RPT-IDN-02 | ⬜ | — |
| RPT-IN-01 | 🟩 | `test_report_and_narrative_return_payloads_and_write_graph_nodes` |
| RPT-IN-02 | ⬜ | — |
| RPT-IN-03 | 🟩 | `test_decisions_ready_triggers_snapshot_ready` |
| RPT-IN-04 | ⬜ | — |
| RPT-TRG-01 | 🟩 | `test_report_and_narrative_return_payloads_and_write_graph_nodes` |
| RPT-TRG-02 | 🟩 | `test_decisions_ready_triggers_snapshot_ready` |
| RPT-TRG-03 | ⬜ | — |
| RPT-TRG-04 | ⬜ | — |
| RPT-OUT-01 | 🟩 | `test_report_and_narrative_return_payloads_and_write_graph_nodes`, `test_snapshot_names_too_little_data_without_raising` |
| RPT-OUT-02 | 🟩 | `test_report_and_narrative_return_payloads_and_write_graph_nodes`, `test_snapshot_reports_profit_factor_and_expectancy` |
| RPT-OUT-03 | 🟩 | `test_reporter_trims_long_narratives_at_configured_limit` |
| RPT-OUT-04 | 🟩 | `test_report_snapshot_result_node_in_graph`, `test_reporter_handles_missing_nodes_without_crashing` |
| RPT-OUT-05 | 🟩 | `test_decisions_ready_triggers_snapshot_ready` |
| RPT-OUT-06 | ⬜ | Demoted S156: `test_reporter_fault_boundary_returns_degraded_payloads` and the renamed degraded-snapshot test cover partial degraded payload behavior, not the full graph-fault/minimal-provenance/empty-metrics/fault-recorded clause. |
| RPT-OUT-07 | 🟩 | `test_performance_worked_example`, `test_performance_inputs_exclude_pre_inception_margin_book`, `test_performance_skips_missing_benchmark_pair_then_continues`, `test_performance_rolling_metrics_use_only_last_configured_pairs` |
| RPT-NEV-01 | 🟩 | `test_reporter_handles_missing_nodes_without_crashing` |
| RPT-NEV-02 | 🟩 | `test_reporter_does_not_import_other_agent_code` |
| RPT-NEV-03 | 🟩 | `test_snapshot_reports_profit_factor_and_expectancy` |
| RPT-STA-01 | ⬜ | — |
| RPT-STA-02 | 🟩 | `test_report_snapshot_result_node_in_graph` |
| RPT-IDM-01 | ⬜ | — |
| RPT-IDM-02 | 🟩 | `test_run_id_propagated_in_snapshot_ready_event` |
| RPT-IDM-03 | 🟩 | `test_performance_inputs_do_not_read_after_pmrun_as_of` |
| RPT-ORD-01 | 🟩 | `test_snapshot_ignores_prior_reporter_performance_output` |
| RPT-ORD-02 | ⬜ | — |
| RPT-FAIL-01 | 🟩 | `test_reporter_fault_boundary_returns_degraded_payloads` |
| RPT-FAIL-02 | ⬜ | — |
| RPT-FAIL-03 | ⬜ | — |
| RPT-FAIL-04 | 🟩 | `test_snapshot_contains_performance_fault_without_losing_other_groups` |
| RPT-TYP-01 | 🟩 | `tests/test_contract_required_fields.py::test_reporter_payload_fields_required_by_law`; `test_report_snapshot_is_deserializable` |
| RPT-TYP-02 | 🟩 | `test_metrics_narrative.py::test_dropped_decision_is_visible_but_not_rejected` |
| RPT-SEC-01 | ⬜ | — |
| RPT-SEC-02 | ⬜ | — |
| RPT-DEP-01 | ⬜ | — |
| RPT-DEP-02 | ⬜ | — |
| RPT-OBS-01 | 🟩 | `test_report_snapshot_result_node_in_graph` |
| RPT-OBS-02 | ⬜ | — |
| RPT-PERF-01 | 🟩 | `test_reporter_trims_long_narratives_at_configured_limit` |
| RPT-PERF-02 | ⬜ | — |
| RPT-CAP | ⬜ | — |
| RPT-TYP-03 | 🟩 | `test_legacy_snapshot_without_performance_metrics_deserializes` |

**Green: 25 / 42**
