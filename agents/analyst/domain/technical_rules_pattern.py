"""Pattern/kernel/calendar scoring rules and their composite contribution.

Agent: analyst
Role: map NW deviation / geometric pattern / turnaround to 0-100 sub-scores.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.domain import indicators_kernel, indicators_pattern

if TYPE_CHECKING:
    from datetime import date

    from agents.analyst.settings import AnalystSettings

# Fixed band cut-points from the sprint spec (the rule itself, not tunable policy);
# named module constants mirroring ``technical_rules_range.py``. Boundaries use strict
# ``<`` / ``>`` so a value equal to a cut-point falls into the neutral band.
_NW_DEV_BAND = 1.0
_NW_BULLISH, _NW_BEARISH = 70.0, 30.0
_PATTERN_BASE, _PATTERN_SWING = 50.0, 30.0
_TURNAROUND_SIGNAL = 75.0
_NEUTRAL = 50.0
_BULLISH_PATTERNS = frozenset(
    {"double_bottom", "inverse_head_and_shoulders", "ascending_triangle"}
)


def score_kernel(deviation_pct: float) -> float:
    """Below the smoothed line is bullish (mean-reversion); overextended is bearish."""
    if deviation_pct < -_NW_DEV_BAND:
        return _NW_BULLISH
    if deviation_pct > _NW_DEV_BAND:
        return _NW_BEARISH
    return _NEUTRAL


def score_pattern(name: str, conf: float) -> float:
    """Bullish patterns lift above neutral; bearish ones drop below, scaled by conf."""
    if name in _BULLISH_PATTERNS:
        return _PATTERN_BASE + conf * _PATTERN_SWING
    return _PATTERN_BASE - conf * _PATTERN_SWING


def score_turnaround(is_signal: bool) -> float:
    """A true Monday turnaround is bullish; every other day is neutral."""
    if is_signal:
        return _TURNAROUND_SIGNAL
    return _NEUTRAL


def pattern_indicator_scores(
    closes: list[float],
    highs: list[float],
    lows: list[float],
    dates: list[date],
    settings: AnalystSettings,
) -> list[tuple[str, float, float]]:
    """Compute and score NW/pattern/turnaround with enough history; skip the rest."""
    scored: list[tuple[str, float, float]] = []
    dev = indicators_kernel.nadaraya_watson(
        closes, settings.nw_bandwidth, settings.nw_lookback
    )
    if dev is not None:
        scored.append(("nw_deviation_pct", dev, score_kernel(dev)))
    pattern = indicators_pattern.geometric_patterns(
        closes, highs, lows, settings.pattern_lookback, settings.pattern_min_swing_pct
    )
    if pattern is not None:
        name, conf = pattern
        scored.append(("geometric_pattern", conf, score_pattern(name, conf)))
    sig = indicators_kernel.turnaround_signal(closes, dates)
    if sig is not None:
        scored.append(("turnaround", 1.0 if sig else 0.0, score_turnaround(sig)))
    return scored
