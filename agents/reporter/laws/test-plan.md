# Reporter — Law Test Plan

| Clause | Status | Test |
| --- | --- | --- |
| RPT-IDN-01 | 🟩 | `test_metrics_narrative.py::test_the_pm_decision_counts_are_reported_as_decided` |
| RPT-IDN-02 | ⬜ | — |
| RPT-IN-01 | 🟩 | `test_report_and_narrative_return_payloads_and_write_graph_nodes`, `test_book_window.py::test_the_runs_snapshot_counts_the_fills_in_its_window` |
| RPT-IN-02 | ⬜ | — |
| RPT-IN-03 | 🟩 | `test_decisions_ready_triggers_snapshot_ready` |
| RPT-IN-04 | ⬜ | — |
| RPT-TRG-01 | 🟩 | `test_report_and_narrative_return_payloads_and_write_graph_nodes` |
| RPT-TRG-02 | 🟩 | `test_decisions_ready_triggers_snapshot_ready`, `test_reporter_poll.py::test_find_pending_returns_unreported_monitor_run`, `test_reporter_poll.py::test_report_monitor_node_writes_snapshot_and_links`, `tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work` |
| RPT-TRG-03 | ⬜ | — |
| RPT-TRG-04 | ⬜ | — |
| RPT-OUT-01 | 🟩 | `test_report_and_narrative_return_payloads_and_write_graph_nodes`, `test_snapshot_names_too_little_data_without_raising` |
| RPT-OUT-02 | 🟩 | `test_report_and_narrative_return_payloads_and_write_graph_nodes`, `test_snapshot_reports_profit_factor_and_expectancy`, `test_book_window.py::test_the_runs_snapshot_counts_the_fills_in_its_window`, `test_book_window.py::test_outcomes_are_cumulative_since_the_inception`, `test_book_window.py::test_a_fill_belongs_to_one_window`, `test_book_window.py::test_the_first_run_has_no_window_start`, `test_book_window_edges.py::test_positions_held_is_the_as_of_snapshots_holdings`, `test_book_window_edges.py::test_the_three_removed_keys_are_gone`, `orchestration/tests/test_reporter_snapshot_readers.py::test_the_trace_and_the_observatory_read_the_new_snapshot` |
| RPT-OUT-03 | 🟩 | `test_reporter_trims_long_narratives_at_configured_limit` |
| RPT-OUT-04 | 🟩 | `test_report_snapshot_result_node_in_graph`, `test_reporter_handles_missing_nodes_without_crashing` |
| RPT-OUT-05 | 🟩 | `test_decisions_ready_triggers_snapshot_ready` |
| RPT-OUT-06 | ⬜ | Demoted S156: `test_reporter_fault_boundary_returns_degraded_payloads` and the renamed degraded-snapshot test cover partial degraded payload behavior, not the full graph-fault/minimal-provenance/empty-metrics/fault-recorded clause. |
| RPT-OUT-07 | 🟩 | `test_performance_worked_example`, `test_performance_inputs_exclude_pre_inception_margin_book`, `test_performance_skips_missing_benchmark_pair_then_continues`, `test_performance_rolling_metrics_use_only_last_configured_pairs`, `test_the_day_point_is_the_latest_fresh_snapshot_of_the_date`, `test_a_two_run_day_uses_the_post_close_sync_not_the_intraday_one`, `test_benchmark_lineage.py::test_a_run_benchmarks_on_its_own_market_data_by_lineage`, `test_benchmark_lineage.py::test_no_benchmark_on_the_runs_own_node_is_the_no_benchmark_path` |
| RPT-NEV-01 | 🟩 | `test_reporter_handles_missing_nodes_without_crashing` |
| RPT-NEV-02 | 🟩 | `test_reporter_does_not_import_other_agent_code` |
| RPT-NEV-03 | 🟩 | `test_snapshot_reports_profit_factor_and_expectancy`, `test_book_window.py::test_outcomes_are_cumulative_since_the_inception`, `test_book_window.py::test_a_run_without_created_at_has_no_book_counts`, `test_book_window_edges.py::test_no_exit_since_the_inception_omits_the_ratios`, `test_book_window_edges.py::test_a_book_read_fault_is_contained`, `orchestration/tests/test_reporter_snapshot_readers.py::test_the_readers_do_not_raise_on_absent_counts`, `test_reporter_handles_missing_nodes_without_crashing` |
| RPT-STA-01 | ⬜ | — |
| RPT-STA-02 | 🟩 | `test_report_snapshot_result_node_in_graph` |
| RPT-IDM-01 | ⬜ | — |
| RPT-IDM-02 | 🟩 | `test_run_id_propagated_in_snapshot_ready_event` |
| RPT-IDM-03 | 🟩 | `test_performance_inputs_do_not_read_after_pmrun_as_of`, `test_a_snapshot_created_after_the_pm_run_is_never_read` |
| RPT-IDM-04 | 🟩 | `test_book_window.py::test_a_fill_belongs_to_one_window`, `test_book_window.py::test_re_reporting_an_old_run_reproduces_its_book_metrics`, `test_book_window_edges.py::test_a_resumed_run_reports_its_sources_window` |
| RPT-ORD-01 | 🟩 | `test_snapshot_ignores_prior_reporter_performance_output` |
| RPT-ORD-02 | ⬜ | — |
| RPT-FAIL-01 | 🟩 | `test_reporter_fault_boundary_returns_degraded_payloads` |
| RPT-FAIL-02 | ⬜ | — |
| RPT-FAIL-03 | ⬜ | — |
| RPT-FAIL-04 | 🟩 | `test_snapshot_contains_performance_fault_without_losing_other_groups` |
| RPT-TYP-01 | 🟩 | `tests/test_contract_required_fields.py::test_reporter_payload_fields_required_by_law`; `test_report_snapshot_is_deserializable` |
| RPT-TYP-02 | 🟩 | `test_metrics_narrative.py::test_the_pm_decision_counts_are_reported_as_decided` |
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

**Green: 26 / 43**
