"""Analyst market-history requirement helpers.

Agent: analyst
Role: derive the price-history depth declared by analyst indicator settings.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class IndicatorHistorySettings(Protocol):
    """Settings fields required to declare the core indicator history window."""

    @property
    def rsi_period(self) -> int:
        """RSI lookback period."""
        ...  # pragma: no cover - protocol declaration only.

    @property
    def macd_slow(self) -> int:
        """MACD slow EMA span."""
        ...  # pragma: no cover - protocol declaration only.

    @property
    def macd_signal(self) -> int:
        """MACD signal EMA span."""
        ...  # pragma: no cover - protocol declaration only.

    @property
    def bollinger_window(self) -> int:
        """Bollinger-band SMA window."""
        ...  # pragma: no cover - protocol declaration only.

    @property
    def sma_long_period(self) -> int:
        """Long SMA period."""
        ...  # pragma: no cover - protocol declaration only.

    @property
    def ema_long_period(self) -> int:
        """Long EMA period."""
        ...  # pragma: no cover - protocol declaration only.


@dataclass(frozen=True)
class IndicatorRequirement:
    """One scored indicator and the bar count it needs before it can compute."""

    metric_name: str
    label: str
    required_bars: int


def momentum_indicator_requirements(
    settings: IndicatorHistorySettings,
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


def required_history_bars(settings: IndicatorHistorySettings) -> int:
    """Return the largest bar requirement among the declared core indicators."""
    return max(
        requirement.required_bars
        for requirement in momentum_indicator_requirements(settings)
    )
