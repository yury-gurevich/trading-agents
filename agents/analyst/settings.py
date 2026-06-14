"""Analyst agent settings and justified scoring tunables.

Agent: analyst
Role: own analyst lookback, indicator, and confidence-model defaults.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator
from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class AnalystSettings(AgentSettings):
    """Settings for deterministic analyst scoring."""

    model_config = SettingsConfigDict(env_prefix="ANALYST_", frozen=True)

    lookback_days: int = tunable(
        260,
        why=(
            "Indicators need up to ~200 trading days of history (SMA200); a "
            "~260-calendar-day window yields enough daily bars."
        ),
        ge=2,
        le=512,
        unit="days",
    )
    min_history_bars: int = tunable(
        2,
        why="At least two closes are required before any indicator is meaningful.",
        ge=2,
        le=60,
        unit="bars",
    )
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
    confidence_floor: float = tunable(
        0.30,
        why="Keep weak but valid technical evidence below the provider regime gate.",
        ge=0.0,
        le=1.0,
    )
    confidence_span: float = tunable(
        0.60,
        why="Let strong technical evidence clear the default 0.60 regime threshold.",
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def _spans_are_ordered(self) -> Self:
        """Reject indicator spans whose fast leg does not trail its slow leg."""
        if self.macd_fast >= self.macd_slow:
            raise ValueError("macd_fast must be below macd_slow")
        if self.ema_short_period >= self.ema_long_period:
            raise ValueError("ema_short_period must be below ema_long_period")
        return self
