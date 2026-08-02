# Supervisor — Law Test Plan

| Clause | Status | Test |
| --- | --- | --- |
| SUP-IDN-01 | ⬜ | — |
| SUP-IDN-02 | 🟩 | `test_approve_intent_resolves_matching_flag` |
| SUP-IN-01 | 🟩 | `test_capability_matrix_routes_available_and_refuses_unavailable` |
| SUP-IN-02 | 🟩 | `test_system_status_reports_empty_fault_flag_and_snapshot_states` |
| SUP-IN-03 | 🟩 | `test_flag_for_human_writes_idempotent_pending_flag` |
| SUP-IN-04 | 🟩 | `test_record_dispatch_run_writes_one_message_per_step` |
| SUP-IN-05 | 🟩 | `test_report_fault_writes_one_fault_node` |
| SUP-IN-06 | ⬜ | — |
| SUP-TRG-01 | ⬜ | — |
| SUP-TRG-02 | ⬜ | — |
| SUP-TRG-03 | ⬜ | — |
| SUP-TRG-04 | ⬜ | — |
| SUP-TRG-05 | ⬜ | — |
| SUP-TRG-06 | ⬜ | — |
| SUP-OUT-01 | 🟩 | `test_capability_matrix_routes_available_and_refuses_unavailable`, `test_approve_intent_resolves_matching_flag`, `test_confirmation_gate_writes_and_resolves_flag` |
| SUP-OUT-02 | 🟩 | `test_system_status_reports_empty_fault_flag_and_snapshot_states` |
| SUP-OUT-03 | 🟩 | `test_flag_for_human_writes_idempotent_pending_flag` |
| SUP-OUT-04 | 🟩 | `test_record_dispatch_run_writes_one_message_per_step` |
| SUP-OUT-05 | 🟩 | `test_report_fault_writes_one_fault_node` |
| SUP-OUT-06 | 🟩 | `test_hard_no_blocks_before_confirmation_or_matrix` |
| SUP-NEV-01 | 🟩 | `test_read_only_status_does_not_write_confirmation_flag` |
| SUP-NEV-02 | 🟩 | `test_hard_no_blocks_before_confirmation_or_matrix` |
| SUP-NEV-03 | 🟩 | `test_capability_matrix_routes_available_and_refuses_unavailable` |
| SUP-NEV-04 | ⬜ | — |
| SUP-STA-01 | ⬜ | — |
| SUP-STA-02 | 🟩 | `test_confirmation_gate_writes_and_resolves_flag`, `test_flag_for_human_writes_idempotent_pending_flag` |
| SUP-IDM-01 | 🟩 | `test_system_status_reports_empty_fault_flag_and_snapshot_states` |
| SUP-IDM-02 | ⬜ | — |
| SUP-ORD-01 | ⬜ | — |
| SUP-ORD-02 | ⬜ | — |
| SUP-FAIL-01 | 🟩 | `test_failure_paths_return_degraded_responses` |
| SUP-FAIL-02 | 🟩 | `test_failure_paths_return_degraded_responses` |
| SUP-FAIL-03 | ⬜ | Demoted S156: `test_record_dispatch_run_returns_rejection_when_graph_write_fails` asserts rejection only, not emitted fault or pipeline-continuation evidence. |
| SUP-FAIL-04 | ⬜ | Demoted S156: `test_report_fault_returns_rejection_when_graph_write_fails` asserts rejection only, not the distinct emitted fault required by the clause. |
| SUP-TYP-01 | ⬜ | — |
| SUP-TYP-02 | ⬜ | — |
| SUP-TYP-03 | ⬜ | — |
| SUP-SEC-01 | ⬜ | — |
| SUP-SEC-02 | 🟩 | `test_capability_matrix_routes_available_and_refuses_unavailable` |
| SUP-SEC-03 | ⬜ | — |
| SUP-SEC-04 | ⬜ | — |
| SUP-DEP-01 | ⬜ | — |
| SUP-DEP-02 | ⬜ | — |
| SUP-OBS-01 | ⬜ | — |
| SUP-OBS-02 | ⬜ | — |
| SUP-OBS-03 | ⬜ | — |
| SUP-PERF-01 | ⬜ | — |
| SUP-PERF-02 | ⬜ | — |
| SUP-CAP | ⬜ | — |

**Green: 21 / 49**
