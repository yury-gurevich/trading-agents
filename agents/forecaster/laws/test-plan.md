# Forecaster — Law Test Plan

| Clause | Status | Test |
| --- | --- | --- |
| FORE-IDN-01 | ⬜ | — |
| FORE-IDN-02 | ⬜ | — |
| FORE-IN-01 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction` |
| FORE-IN-02 | ⬜ | Demoted S156: `test_forecast_return_persists_and_returns_a_shadow_prediction` proves a shadow prediction is returned and persisted, not that forecast_return ignores request features while fetching OHLCV via the provider bus. |
| FORE-IN-03 | 🟩 | `test_scorecard_reports_samples_and_never_promotes` |
| FORE-IN-04 | ⬜ | — |
| FORE-IN-05 | ⬜ | — |
| FORE-IN-06 | ⬜ | — |
| FORE-TRG-01 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction` |
| FORE-TRG-02 | 🟩 | `test_served_forecast_is_request_triggered_shadow_only` |
| FORE-OUT-01 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction` |
| FORE-OUT-02 | 🟩 | `test_every_forecast_is_a_shadow_signal`, `test_served_forecast_is_request_triggered_shadow_only` |
| FORE-OUT-03 | 🟩 | `test_scorecard_reports_samples_and_never_promotes`, `test_generic_scorecard_covers_factor_predictions_and_never_promotes` |
| FORE-OUT-04 | 🟩 | `test_scorecard_is_never_promotion_eligible`, `test_scorecard_reports_samples_and_never_promotes`, `test_generic_scorecard_covers_factor_predictions_and_never_promotes` |
| FORE-OUT-05 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction` |
| FORE-OUT-06 | 🟩 | `test_forecast_with_no_news_is_neutral_zero_confidence` |
| FORE-NEV-01 | 🟩 | `test_every_forecast_is_a_shadow_signal`, `test_contract_declares_never_clauses_and_no_external_io` |
| FORE-NEV-02 | 🟩 | `test_contract_declares_never_clauses_and_no_external_io`, `test_served_forecast_is_request_triggered_shadow_only`, `test_forecast_factor_enabled_writes_shadow_only_prediction` |
| FORE-NEV-03 | 🟩 | `test_scorecard_is_never_promotion_eligible`, `test_contract_declares_never_clauses_and_no_external_io` |
| FORE-NEV-04 | 🟩 | `test_forecast_survives_a_provider_fault` |
| FORE-STA-01 | ⬜ | — |
| FORE-STA-02 | ⬜ | — |
| FORE-IDM-01 | ⬜ | — |
| FORE-IDM-02 | ⬜ | — |
| FORE-IDM-03 | ⬜ | — |
| FORE-ORD-01 | ⬜ | — |
| FORE-ORD-02 | ⬜ | — |
| FORE-FAIL-01 | 🟩 | `test_forecast_falls_back_to_neutral_on_a_model_fault` |
| FORE-FAIL-02 | 🟩 | `test_forecast_survives_a_provider_fault` |
| FORE-FAIL-03 | ⬜ | Demoted S156: `test_forecast_return_falls_back_to_neutral_on_a_model_fault` covers a generic injected model exception, not the specific missing-LightGBM-file clause. |
| FORE-TYP-01 | ⬜ | — |
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

## **Green: 16 / 46**
