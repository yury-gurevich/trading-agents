# Operator — Law Test Plan

| Clause | Status | Test |
| --- | --- | --- |
| OPR-IDN-01 | ⬜ | — |
| OPR-IDN-02 | 🟩 | `test_operator_boundary_claims_graph_labels_once`; `test_operator_does_not_claim_llmcall_as_a_single_writer_label` (ADR-0020 exclusion) |
| OPR-IN-01 | 🟩 | `test_interpret_maps_all_ten_families_with_confirmation_policy` |
| OPR-IN-02 | 🟩 | `test_explain_returns_text_and_writes_audit_and_llm_call` |
| OPR-IN-03 | 🟩 | `test_interpret_llm_exception_returns_refusal` |
| OPR-IN-04 | ⬜ | — |
| OPR-TRG-01 | ⬜ | — |
| OPR-TRG-02 | ⬜ | — |
| OPR-TRG-03 | ⬜ | — |
| OPR-OUT-01 | 🟩 | `test_interpret_maps_all_ten_families_with_confirmation_policy` |
| OPR-OUT-02 | ⬜ | — |
| OPR-OUT-03 | ⬜ | — |
| OPR-OUT-04 | 🟩 | `test_explain_returns_text_and_writes_audit_and_llm_call` |
| OPR-OUT-05 | 🟩 | `test_interpret_malformed_refused_and_clarification_paths` |
| OPR-OUT-06 | 🟩 | `test_interpret_maps_all_ten_families_with_confirmation_policy`, `test_explain_returns_text_and_writes_audit_and_llm_call` |
| OPR-OUT-07 | 🟩 | `test_interpret_maps_all_ten_families_with_confirmation_policy` |
| OPR-NEV-01 | 🟩 | `test_interpret_invalid_intent_family_is_refused` |
| OPR-NEV-02 | ⬜ | — |
| OPR-NEV-03 | ⬜ | — |
| OPR-NEV-04 | ⬜ | — |
| OPR-NEV-05 | 🟩 | `test_interpret_malformed_refused_and_clarification_paths` |
| OPR-NEV-06 | ⬜ | — |
| OPR-STA-01 | ⬜ | — |
| OPR-STA-02 | ⬜ | — |
| OPR-STA-03 | 🟩 | Every call records model, prompt, response and timestamp; the vendor's stop reason and counts survive finished and cut-off replies; clients exposing neither retain unknown with a stamped estimate: `test_explain_returns_text_and_writes_audit_and_llm_call`; `agents/operator/tests/test_cutoff_adapter.py::test_a1_anthropic_cutoff_records_metadata_before_raising`; `test_a2_finished_anthropic_reply_keeps_its_stop_reason`; `test_a4_failed_request_clears_anthropic_metadata`; `agents/operator/tests/test_cutoff_ledger.py::test_b1_cutoff_helper_records_usage_and_error_stop_reason`; `test_b2_finished_helper_records_response_stop_and_usage`; `test_b3_client_without_metadata_uses_stamped_estimates`; `agents/operator/tests/test_cutoff_agent.py::test_c1_cutoff_explain_audits_before_returning_the_sentence`; `test_c4_finished_call_records_the_clients_stop_reason` |
| OPR-IDM-01 | ⬜ | — |
| OPR-IDM-02 | 🟩 | Duplicate commands without request ids share one correlation, audit and intent, but every model call appends its own LLMCall (first correlation key, later :repeat-N): `test_same_command_shares_audit_and_intent_and_records_each_call`; `test_write_llm_call_records_operator_attribution` |
| OPR-IDM-03 | 🟩 | `test_same_command_shares_audit_and_intent_and_records_each_call` |
| OPR-ORD-01 | ⬜ | — |
| OPR-ORD-02 | ⬜ | — |
| OPR-FAIL-01 | 🟩 | `test_interpret_llm_exception_returns_refusal` |
| OPR-FAIL-02 | 🟩 | `test_interpret_invalid_intent_family_is_refused` |
| OPR-FAIL-03 | ⬜ | — |
| OPR-FAIL-04 | 🟩 | A vendor cut-off is neither a fault nor an answer; recorded under OPR-STA-03; interpret refuses with CUT_OFF_REPLY through the explicit grammar; explain returns that sentence; no partial reply is shown; CommandAudit links to LLMCall as for any reply, on every vendor: `agents/operator/tests/test_cutoff_agent.py::test_c1_cutoff_explain_audits_before_returning_the_sentence`; `test_c2_cutoff_interpret_refuses_with_reason_and_linked_audit`; `test_c3_explicit_approve_keeps_grammar_after_cutoff`; `test_c6_cutoff_sentence_is_pinned_letter_for_letter`; `surfaces/tests/test_chat_cutoff.py::test_d1_cutoff_chat_is_equal_on_both_vendors`; `test_d2_partial_tool_answer_is_never_shown`; `test_d3_outage_distinguishes_failed_request_from_cutoff` |
| OPR-TYP-01 | 🟩 | `tests/test_contract_required_fields.py::test_operator_payload_fields_required_by_law` |
| OPR-TYP-02 | ⬜ | — |
| OPR-TYP-03 | ⬜ | — |
| OPR-SEC-01 | 🟩 | `tests/test_llm_adapter_security.py::test_anthropic_key_never_escapes_deliberator_or_operator` |
| OPR-SEC-02 | ⬜ | — |
| OPR-SEC-03 | ⬜ | — |
| OPR-SEC-04 | ⬜ | — |
| OPR-SEC-05 | ⬜ | — |
| OPR-DEP-01 | 🟩 | Declared provider or injected fake is the sole external call, never a fallback; empty model and effort resolve the provider defaults, explicit values pass as set, and another provider's model family is refused before any call: `tests/test_operator_llm_factory.py::test_b4_factory_builds_exactly_selected_vendor`; `test_b4_selected_failure_never_builds_other_vendor`; `test_b4_unknown_provider_refuses`; `test_provider_model.py::test_b1_model_follows_provider_and_override`; `tests/test_operator_provider_guards.py::test_b1_effort_follows_provider`; `test_b2_unknown_provider_effort`; `test_b3_mismatched_model_builds_nothing`; `test_b4_unknown_model_family_is_vendors_to_judge`; `tests/test_operator_responses_wire.py::test_a8_captured_wire_replay`; `tests/test_openai_operator_security.py::test_b6_openai_key_never_escapes_operator`; existing Anthropic constructor proof remains applicable to that selection |
| OPR-DEP-02 | ⬜ | — |
| OPR-DEP-03 | ⬜ | — |
| OPR-OBS-01 | ⬜ | — |
| OPR-OBS-02 | ⬜ | — |
| OPR-OBS-03 | ⬜ | — |
| OPR-PERF-01 | ⬜ | — |
| OPR-PERF-02 | ⬜ | — |
| OPR-PERF-03 | ⬜ | — |
| OPR-CAP | ⬜ | — |

## Green: 20 / 51
