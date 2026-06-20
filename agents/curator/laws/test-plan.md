# Curator — Law Test Plan

| Clause | Status | Test |
| --- | --- | --- |
| CUR-IDN-01 | ⬜ | — |
| CUR-IDN-02 | 🟩 | `test_build_dataset_writes_nodes_edges_and_payload` |
| CUR-IN-01 | 🟩 | `test_build_dataset_writes_nodes_edges_and_payload` |
| CUR-IN-02 | 🟩 | `test_describe_corpus_summarises_counts` |
| CUR-IN-03 | 🟩 | `test_train_predictor_writes_advisory_predictor` |
| CUR-IN-04 | 🟩 | `test_passing_evidence_first_call_pends_with_flag` |
| CUR-IN-05 | ⬜ | — |
| CUR-TRG-01 | 🟩 | `test_build_dataset_writes_nodes_edges_and_payload` |
| CUR-TRG-02 | ⬜ | — |
| CUR-TRG-03 | ⬜ | — |
| CUR-OUT-01 | 🟩 | `test_build_dataset_writes_nodes_edges_and_payload` |
| CUR-OUT-02 | 🟩 | `test_describe_corpus_summarises_counts` |
| CUR-OUT-03 | 🟩 | `test_train_predictor_writes_advisory_predictor` |
| CUR-OUT-04 | 🟩 | `test_train_predictor_writes_advisory_predictor` |
| CUR-OUT-05 | 🟩 | `test_passing_evidence_first_call_pends_with_flag`, `test_promote_after_approval_writes_audit` |
| CUR-OUT-06 | ⬜ | — |
| CUR-NEV-01 | 🟩 | `test_curator_build_dataset_mutates_no_decision_node` |
| CUR-NEV-02 | 🟩 | `test_low_accuracy_rejected_without_flag` |
| CUR-NEV-03 | 🟩 | `test_curator_build_dataset_mutates_no_decision_node` |
| CUR-NEV-04 | 🟩 | `test_empty_corpus_degrades_without_crash` |
| CUR-STA-01 | ⬜ | — |
| CUR-STA-02 | ⬜ | — |
| CUR-STA-03 | ⬜ | — |
| CUR-IDM-01 | ⬜ | — |
| CUR-IDM-02 | 🟩 | `test_second_build_increments_version` |
| CUR-IDM-03 | ⬜ | — |
| CUR-ORD-01 | ⬜ | — |
| CUR-ORD-02 | ⬜ | — |
| CUR-ORD-03 | ⬜ | — |
| CUR-FAIL-01 | 🟩 | `test_build_dataset_degrades_on_graph_fault` |
| CUR-FAIL-02 | ⬜ | — |
| CUR-FAIL-03 | 🟩 | `test_train_predictor_degrades_on_graph_fault` |
| CUR-FAIL-04 | 🟩 | `test_low_accuracy_rejected_without_flag` |
| CUR-FAIL-05 | 🟩 | `test_empty_corpus_degrades_without_crash` |
| CUR-TYP-01 | ⬜ | — |
| CUR-TYP-02 | ⬜ | — |
| CUR-TYP-03 | ⬜ | — |
| CUR-SEC-01 | ⬜ | — |
| CUR-SEC-02 | ⬜ | — |
| CUR-SEC-03 | 🟩 | `test_passing_evidence_first_call_pends_with_flag` |
| CUR-DEP-01 | ⬜ | — |
| CUR-DEP-02 | ⬜ | — |
| CUR-OBS-01 | ⬜ | — |
| CUR-OBS-02 | 🟩 | `test_promote_after_approval_writes_audit` |
| CUR-OBS-03 | ⬜ | — |
| CUR-PERF-01 | ⬜ | — |
| CUR-PERF-02 | ⬜ | — |
| CUR-CAP | ⬜ | — |

**Green: 20 / 48**
