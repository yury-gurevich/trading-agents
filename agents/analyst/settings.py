"""Analyst agent settings and justified scoring tunables.

Agent: analyst
Role: own analyst lookback, history, and confidence-model defaults.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator
from pydantic_settings import SettingsConfigDict

from agents.analyst.settings_indicators import _IndicatorSettings
from kernel import tunable


class AnalystSettings(_IndicatorSettings):
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
    technical_weight: float = tunable(
        0.50,
        why="Reference composite weight for the technical pillar.",
        ge=0.0,
        le=1.0,
    )
    fundamental_weight: float = tunable(
        0.30,
        why=(
            "Reference composite weight for the fundamental pillar; renormalised "
            "over present pillars."
        ),
        ge=0.0,
        le=1.0,
    )
    benchmark_ticker: str = tunable(
        "SPY",
        why="Relative-strength benchmark; SPY tracks the scanner's S&P 500 universe.",
    )
    rs_window: int = tunable(
        20,
        why="Reference relative-strength lookback (~one trading month).",
        ge=2,
        le=120,
        unit="bars",
    )
    relative_strength_weight: float = tunable(
        0.20,
        why=(
            "Reference weight of relative strength within the technical pillar "
            "(0.8 technical / 0.2 relative strength)."
        ),
        ge=0.0,
        le=1.0,
    )
    signal_diversity_slack: float = tunable(
        5.0,
        why=(
            "Contribution slack letting a lower-scoring signal from an unused pillar "
            "be surfaced ahead of another from a pillar already represented."
        ),
        ge=0.0,
        le=50.0,
    )
    max_top_signals: int = tunable(
        5,
        why="Maximum explanatory signals surfaced per recommendation rationale.",
        ge=1,
        le=20,
    )

    @model_validator(mode="after")
    def _spans_are_ordered(self) -> Self:
        """Reject indicator spans whose fast leg does not trail its slow leg."""
        if self.macd_fast >= self.macd_slow:
            raise ValueError("macd_fast must be below macd_slow")
        if self.ema_short_period >= self.ema_long_period:
            raise ValueError("ema_short_period must be below ema_long_period")
        return self
