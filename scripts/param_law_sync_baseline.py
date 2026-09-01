"""Legacy PARAM/settings reconciliation baseline.

Agent: tooling
Role: name known pre-S187 PARAM/settings gaps that remain warning-only.
External I/O: none; exports immutable checker constants.
"""

from __future__ import annotations

IssueKey = tuple[str, str, str]

MISSING_PARAM = "settings field has no PARAM row"
MISSING_SETTING = "PARAM row has no settings field"
TUNABLE_MISMATCH = "Tunable column disagrees with settings metadata"

LEGACY_BASELINE: frozenset[IssueKey] = frozenset(
    {
        ("analyst", MISSING_PARAM, "atr_period"),
        ("analyst", MISSING_PARAM, "bollinger_sigma"),
        ("analyst", MISSING_PARAM, "bollinger_window"),
        ("analyst", MISSING_PARAM, "choppiness_period"),
        ("analyst", MISSING_PARAM, "ema_long_period"),
        ("analyst", MISSING_PARAM, "ema_short_period"),
        ("analyst", MISSING_PARAM, "exit_confidence_floor"),
        ("analyst", MISSING_PARAM, "golden_cross_short_period"),
        ("analyst", MISSING_PARAM, "macd_fast"),
        ("analyst", MISSING_PARAM, "macd_signal"),
        ("analyst", MISSING_PARAM, "macd_slow"),
        ("analyst", MISSING_PARAM, "nw_bandwidth"),
        ("analyst", MISSING_PARAM, "nw_lookback"),
        ("analyst", MISSING_PARAM, "obv_signal_period"),
        ("analyst", MISSING_PARAM, "pattern_lookback"),
        ("analyst", MISSING_PARAM, "pattern_min_swing_pct"),
        ("analyst", MISSING_PARAM, "rsi2_period"),
        ("analyst", MISSING_PARAM, "rsi_period"),
        ("analyst", MISSING_PARAM, "sma_long_period"),
        ("analyst", MISSING_PARAM, "stoch_d_period"),
        ("analyst", MISSING_PARAM, "stoch_k_period"),
        ("analyst", MISSING_PARAM, "williams_period"),
        ("deliberator", MISSING_PARAM, "llm_provider"),
        ("execution", MISSING_SETTING, "close_quantity"),
        ("execution", MISSING_SETTING, "close_reference_price"),
        ("forecaster", MISSING_PARAM, "factor_model_id"),
        ("forecaster", MISSING_PARAM, "factor_name"),
        ("forecaster", MISSING_PARAM, "factor_params"),
        ("forecaster", MISSING_PARAM, "retrain_horizon_days"),
        ("forecaster", MISSING_PARAM, "retrain_min_cases"),
        ("forecaster", MISSING_PARAM, "retrain_trigger_fraction"),
        ("forecaster", MISSING_PARAM, "retrain_window_days"),
        ("master", MISSING_PARAM, "auto_remediation_scope"),
        ("master", MISSING_PARAM, "grant_policy_b64"),
        ("master", MISSING_PARAM, "grant_policy_path"),
        ("master", MISSING_PARAM, "max_auto_remediation_attempts"),
        ("master", MISSING_PARAM, "remediation_mode"),
        ("master", MISSING_PARAM, "secret_cache_ttl_minutes"),
        ("master", MISSING_PARAM, "secret_map_b64"),
        ("master", MISSING_PARAM, "secret_map_path"),
        ("portfolio_manager", MISSING_SETTING, "issuer_map"),
        ("provider", MISSING_PARAM, "alpaca_api_key"),
        ("provider", MISSING_PARAM, "alpaca_api_secret"),
        ("provider", MISSING_PARAM, "alpaca_data_base_url"),
        ("provider", MISSING_PARAM, "alpaca_data_timeout"),
        ("provider", MISSING_PARAM, "alphavantage_api_key"),
        ("provider", MISSING_PARAM, "finnhub_api_key"),
        ("provider", MISSING_PARAM, "finnhub_earnings_lookahead_days"),
        ("provider", MISSING_PARAM, "fmp_api_key"),
        ("provider", MISSING_PARAM, "fred_api_key"),
        ("provider", MISSING_PARAM, "ingest_chunk_delay_seconds"),
        ("provider", MISSING_PARAM, "ingest_chunk_size"),
        ("provider", MISSING_PARAM, "tiingo_api_key"),
        ("researcher", MISSING_PARAM, "backtest_holdout_fraction"),
        ("researcher", MISSING_PARAM, "backtest_slippage_bps"),
        ("researcher", MISSING_PARAM, "backtest_top_k"),
        ("scanner", MISSING_PARAM, "bypass_scanner_filter"),
    }
)
