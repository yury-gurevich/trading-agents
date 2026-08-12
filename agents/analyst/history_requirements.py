"""Analyst market-history requirement helpers.

Agent: analyst
Role: derive the price-history depth declared by analyst indicator settings.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings


@dataclass(frozen=True)
class IndicatorRequirement:
    """One scored indicator and the bar count it needs before it can compute."""

    metric_name: str
    label: str
    required_bars: int


def momentum_indicator_requirements(
    settings: AnalystSettings,
) -> tuple[IndicatorRequirement, ...]:
    """Return the five core momentum/trend indicators and their declared windows."""
    return (
        IndicatorRequirement("rsi", "RSI", settings.rsi_period + 1),
        IndicatorRequirement(
            "macd_histogram",
            "MACD",
            settings.macd_slow + settings.macd_signal,
        ),
        IndicatorRequirement(
            "bollinger_position",
            "Bollinger",
            settings.bollinger_window,
        ),
        IndicatorRequirement(
            "sma_distance_pct",
            "SMA-200 distance",
            settings.sma_long_period,
        ),
        IndicatorRequirement(
            "ema_spread_pct",
            "EMA crossover",
            settings.ema_long_period,
        ),
    )


def required_history_bars(settings: AnalystSettings) -> int:
    """Return the largest bar requirement among the declared core indicators."""
    return max(
        requirement.required_bars
        for requirement in momentum_indicator_requirements(settings)
    )
