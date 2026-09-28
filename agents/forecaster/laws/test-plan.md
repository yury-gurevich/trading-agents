# Forecaster — Law Test Plan

| Clause | Status | Test |
| --- | --- | --- |
| FORE-IDN-01 | ⬜ | — |
| FORE-IDN-02 | 🟩 | `test_a_successful_call_writes_one_complete_claim`, `test_the_claim_passes_the_packs_vocabulary_guard` |
| FORE-IN-01 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction` |
| FORE-IN-02 | ⬜ | Demoted S156: `test_forecast_return_persists_and_returns_a_shadow_prediction` proves a shadow prediction is returned and persisted, not that forecast_return ignores request features while fetching OHLCV via the provider bus. |
| FORE-IN-03 | 🟩 | `test_scorecard_reports_samples_and_never_promotes` |
| FORE-IN-04 | ⬜ | — |
| FORE-IN-05 | ⬜ | — |
| FORE-IN-06 | ⬜ | — |
| FORE-IN-07 | 🟩 | `test_malformed_barriers_record_no_claim`, `test_the_history_is_one_long_ohlcv_request_to_the_provider`, `test_the_poll_asks_for_a_claim_only_for_buys_with_both_barriers` |
| FORE-TRG-01 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction` |
| FORE-TRG-02 | 🟩 | `test_served_forecast_is_request_triggered_shadow_only` |
| FORE-OUT-01 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction` |
| FORE-OUT-02 | 🟩 | `test_every_forecast_is_a_shadow_signal`, `test_served_forecast_is_request_triggered_shadow_only` |
| FORE-OUT-03 | 🟩 | `test_scorecard_reports_samples_and_never_promotes`, `test_generic_scorecard_covers_factor_predictions_and_never_promotes` |
| FORE-OUT-04 | 🟩 | `test_scorecard_is_never_promotion_eligible`, `test_scorecard_reports_samples_and_never_promotes`, `test_generic_scorecard_covers_factor_predictions_and_never_promotes` |
| FORE-OUT-05 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction` |
| FORE-OUT-06 | 🟩 | `test_forecast_with_no_news_is_neutral_zero_confidence` |
| FORE-OUT-07 | 🟩 | `test_a_rising_history_reaches_the_target_first`, `test_a_falling_history_reaches_the_stop_first`, `test_a_flat_history_with_wide_barriers_reaches_neither`, `test_a_session_touching_both_barriers_counts_as_the_stop`, `test_the_simulation_equals_exp018`, `test_a_successful_call_writes_one_complete_claim`, `test_a_full_pass_never_reaches_the_decision_path` |
| FORE-NEV-01 | 🟩 | `test_every_forecast_is_a_shadow_signal`, `test_contract_declares_never_clauses_and_no_external_io` |
| FORE-NEV-02 | 🟩 | `test_contract_declares_never_clauses_and_no_external_io`, `test_served_forecast_is_request_triggered_shadow_only`, `test_forecast_factor_enabled_writes_shadow_only_prediction` |
| FORE-NEV-03 | 🟩 | `test_scorecard_is_never_promotion_eligible`, `test_contract_declares_never_clauses_and_no_external_io` |
| FORE-NEV-04 | 🟩 | `test_forecast_survives_a_provider_fault` |
| FORE-STA-01 | ⬜ | — |
| FORE-STA-02 | ⬜ | — |
| FORE-IDM-01 | ⬜ | — |
| FORE-IDM-02 | ⬜ | — |
| FORE-IDM-03 | ⬜ | — |
| FORE-IDM-04 | 🟩 | `test_the_same_bars_give_the_same_claim_merged_into_one_node`, `test_a_different_claim_for_the_same_last_bar_is_refused`, `test_the_seed_is_stable_across_processes` |
| FORE-ORD-01 | ⬜ | — |
| FORE-ORD-02 | ⬜ | — |
| FORE-FAIL-01 | 🟩 | `test_forecast_falls_back_to_neutral_on_a_model_fault` |
| FORE-FAIL-02 | 🟩 | `test_forecast_survives_a_provider_fault` |
| FORE-FAIL-03 | ⬜ | Demoted S156: `test_forecast_return_falls_back_to_neutral_on_a_model_fault` covers a generic injected model exception, not the specific missing-LightGBM-file clause. |
| FORE-FAIL-04 | 🟩 | `test_a_fit_is_accepted_or_capped_as_exp018_did`, `test_the_boundary_tolerance_is_exp018s`, `test_every_other_fit_fails`, `test_a_failed_fit_records_no_claim`, `test_a_fitter_exception_records_no_claim`, `test_short_history_records_no_claim_and_never_fits`, `test_a_provider_error_records_no_claim`, `test_without_arch_the_default_fitter_records_no_claim` |
| FORE-TYP-01 | 🟩 | `tests/test_contract_required_payload_fields.py::test_forecaster_payload_fields_required_by_law` |
| FORE-TYP-02 | ⬜ | — |
| FORE-TYP-03 | ⬜ | — |
| FORE-SEC-01 | ⬜ | — |
| FORE-SEC-02 | ⬜ | — |
| FORE-SEC-03 | ⬜ | — |
| FORE-DEP-01 | ⬜ | — |
| FORE-DEP-02 | ⬜ | — |
| FORE-DEP-03 | ⬜ | — |
| FORE-OBS-01 | ⬜ | — |
| FORE-OBS-02 | ⬜ | — |
| FORE-OBS-03 | ⬜ | — |
| FORE-PERF-01 | ⬜ | — |
| FORE-PERF-02 | ⬜ | — |
| FORE-PERF-03 | ⬜ | — |
| FORE-CAP | ⬜ | — |

## **Green: 22 / 49**
