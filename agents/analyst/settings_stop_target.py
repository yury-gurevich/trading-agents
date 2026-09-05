"""Analyst stop/target mode selector and volatility-scaling tunables.

Agent: analyst
Role: own the ADR-0013 stop/target mode selector, its scaling knobs, and the
      horizon the realized-drawdown record covers (`ANLZ-OBS-05`).
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from typing import Literal

from agents.analyst.settings_indicators import _IndicatorSettings
from kernel import tunable

StopTargetMode = Literal["flat", "scaled"]


class _StopTargetSettings(_IndicatorSettings):
    """Stop/target mode and scaling tunables; never instantiated directly."""

    stop_target_mode: StopTargetMode = "flat"
    stop_target_drawdown_horizon_days: int = tunable(
        10,
        why=(
            "Sessions after a recommendation over which its realized adverse "
            "excursion is measured (ANLZ-OBS-05). Ten sessions is long enough for "
            "an ordinary stop to be touched by noise and short enough that most "
            "recommendations settle inside the run's own lookback; the recorded "
            "value always carries the horizon it used, so changing this cannot "
            "silently reinterpret history."
        ),
        ge=1,
        le=60,
        unit="sessions",
    )
    scaled_stop_atr_multiplier: float = tunable(
        2.0,
        why=(
            "Measure a challenger stop near two times decision-time ATR; S150 "
            "evidence showed this equalizes ordinary touch rates before the "
            "risk cap clamps the widest names."
        ),
        ge=0.0,
        le=5.0,
        unit="ratio",
    )
    scaled_stop_floor_pct: float = tunable(
        0.025,
        why=(
            "Keep volatility-scaled stops from becoming too tight on very quiet "
            "or tiny-ATR names while still allowing a narrower-than-flat challenger."
        ),
        ge=0.0,
        le=0.08,
        unit="pct",
    )
    scaled_stop_ceiling_pct: float = tunable(
        0.08,
        why=(
            "Respect the current PRD/regime maximum stop risk; the challenger must "
            "not silently widen a stop past the system's declared risk cap."
        ),
        ge=0.0,
        le=0.08,
        unit="pct",
    )
