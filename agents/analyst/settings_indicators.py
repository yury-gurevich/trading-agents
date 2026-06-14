"""Analyst indicator-period and window tunables (the calculation knobs).

Agent: analyst
Role: own the justified periods/windows the technical indicators are computed over.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from kernel import AgentSettings, tunable


class _IndicatorSettings(AgentSettings):
    """Indicator period/window tunables; never instantiated directly."""

    rsi_period: int = tunable(
        14,
        why="Wilder's canonical RSI lookback; the technical-analysis standard.",
        ge=2,
        le=100,
        unit="bars",
    )
    macd_fast: int = tunable(
        12,
        why="Standard MACD fast EMA span from the reference indicator definition.",
        ge=2,
        le=100,
        unit="bars",
    )
    macd_slow: int = tunable(
        26,
        why="Standard MACD slow EMA span; must exceed the fast span.",
        ge=3,
        le=200,
        unit="bars",
    )
    macd_signal: int = tunable(
        9,
        why="Standard MACD signal EMA span over the MACD line.",
        ge=2,
        le=100,
        unit="bars",
    )
    bollinger_window: int = tunable(
        20,
        why="Standard Bollinger-band SMA window from the reference definition.",
        ge=2,
        le=200,
        unit="bars",
    )
    bollinger_sigma: float = tunable(
        2.0,
        why="Standard two-standard-deviation Bollinger band width.",
        ge=0.5,
        le=4.0,
    )
    sma_long_period: int = tunable(
        200,
        why="The 200-day SMA is the conventional long-term trend reference.",
        ge=20,
        le=400,
        unit="bars",
    )
    ema_short_period: int = tunable(
        20,
        why="Fast EMA leg of the crossover trend signal; must trail the long leg.",
        ge=2,
        le=200,
        unit="bars",
    )
    ema_long_period: int = tunable(
        50,
        why="Slow EMA leg of the crossover trend signal; the trend baseline.",
        ge=3,
        le=400,
        unit="bars",
    )
    atr_period: int = tunable(
        14,
        why="Wilder's canonical Average True Range lookback (volatility).",
        ge=2,
        le=100,
        unit="bars",
    )
    stoch_k_period: int = tunable(
        14,
        why="Standard stochastic %K lookback window.",
        ge=2,
        le=100,
        unit="bars",
    )
    stoch_d_period: int = tunable(
        3,
        why="Standard stochastic %D smoothing over the %K series.",
        ge=1,
        le=20,
        unit="bars",
    )
    williams_period: int = tunable(
        14,
        why="Standard Williams %R lookback window.",
        ge=2,
        le=100,
        unit="bars",
    )
    choppiness_period: int = tunable(
        14,
        why="Standard Choppiness Index lookback window.",
        ge=2,
        le=100,
        unit="bars",
    )
    obv_signal_period: int = tunable(
        20,
        why="Smoothing window for the OBV signal line the rule compares against.",
        ge=2,
        le=100,
        unit="bars",
    )
    golden_cross_short_period: int = tunable(
        50,
        why="Fast SMA leg of the 50/200 golden cross; the long leg reuses sma_long.",
        ge=2,
        le=200,
        unit="bars",
    )
    rsi2_period: int = tunable(
        2,
        why="Connors' short RSI lookback for the mean-reversion oversold signal.",
        ge=2,
        le=10,
        unit="bars",
    )
    nw_bandwidth: float = tunable(
        8.0,
        why="Gaussian kernel width for the Nadaraya-Watson price smoother.",
        ge=0.5,
        le=50.0,
    )
    nw_lookback: int = tunable(
        50,
        why="Window the Nadaraya-Watson kernel estimate is computed over.",
        ge=10,
        le=200,
        unit="bars",
    )
    pattern_lookback: int = tunable(
        60,
        why="Window the geometric chart-pattern swing search scans.",
        ge=20,
        le=200,
        unit="bars",
    )
    pattern_min_swing_pct: float = tunable(
        2.0,
        why="Swing significance and pattern matching tolerance, in percent.",
        ge=0.5,
        le=10.0,
    )
