"""Range-indicator scoring rules and their composite contribution.

Agent: analyst
Role: map ATR/Stochastic/Williams/Choppiness values to 0-100 sub-scores.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.domain import indicators_range

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings

# Fixed band cut-points from the sprint spec (the rule itself, not tunable policy);
# named module constants mirroring ``technical_rules.py``. Boundaries use strict
# ``<`` / ``>`` so a value equal to a cut-point falls into the neutral band.
_ATR_LOW_PCT, _ATR_HIGH_PCT = 2.0, 4.0
_ATR_SCORES = (70.0, 55.0, 35.0)
_STOCH_OVERSOLD, _STOCH_OVERBOUGHT = 20.0, 80.0
_STOCH_SCORES = (80.0, 65.0, 20.0, 35.0)
_WILLIAMS_OVERSOLD, _WILLIAMS_OVERBOUGHT = -80.0, -20.0
_WILLIAMS_SCORES = (75.0, 25.0)
_CHOP_TRENDING, _CHOP_CHOPPY = 38.2, 61.8
_CHOP_SCORES = (75.0, 30.0)
_NEUTRAL = 50.0


def score_atr(atr_pct: float) -> float:
    """Lower realized volatility (ATR as a percent of price) scores higher."""
    if atr_pct < _ATR_LOW_PCT:
        return _ATR_SCORES[0]
    if atr_pct < _ATR_HIGH_PCT:
        return _ATR_SCORES[1]
    return _ATR_SCORES[2]


def score_stochastic(percent_k: float, percent_d: float) -> float:
    """Oversold (both lines low) is bullish; overbought (both high) is bearish."""
    if percent_k < _STOCH_OVERSOLD and percent_d < _STOCH_OVERSOLD:
        return _STOCH_SCORES[0]
    if percent_k < _STOCH_OVERSOLD:
        return _STOCH_SCORES[1]
    if percent_k > _STOCH_OVERBOUGHT and percent_d > _STOCH_OVERBOUGHT:
        return _STOCH_SCORES[2]
    if percent_k > _STOCH_OVERBOUGHT:
        return _STOCH_SCORES[3]
    return _NEUTRAL


def score_williams(value: float) -> float:
    """Oversold (%R below -80) is bullish; overbought (above -20) is bearish."""
    if value < _WILLIAMS_OVERSOLD:
        return _WILLIAMS_SCORES[0]
    if value > _WILLIAMS_OVERBOUGHT:
        return _WILLIAMS_SCORES[1]
    return _NEUTRAL


def score_choppiness(value: float) -> float:
    """A trending market (low CI) is favourable; a choppy one (high CI) is not."""
    if value < _CHOP_TRENDING:
        return _CHOP_SCORES[0]
    if value > _CHOP_CHOPPY:
        return _CHOP_SCORES[1]
    return _NEUTRAL


def range_indicator_scores(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    settings: AnalystSettings,
) -> list[tuple[str, float, float]]:
    """Compute and score every range indicator with enough history; skip the rest."""
    scored: list[tuple[str, float, float]] = []
    atr = indicators_range.atr(highs, lows, closes, settings.atr_period)
    if atr is not None:
        atr_pct = atr / closes[-1] * 100.0
        scored.append(("atr_pct", atr_pct, score_atr(atr_pct)))
    stoch = indicators_range.stochastic(
        highs, lows, closes, settings.stoch_k_period, settings.stoch_d_period
    )
    if stoch is not None:
        scored.append(("stochastic_k", stoch[0], score_stochastic(stoch[0], stoch[1])))
    williams = indicators_range.williams_r(
        highs, lows, closes, settings.williams_period
    )
    if williams is not None:
        scored.append(("williams_r", williams, score_williams(williams)))
    chop = indicators_range.choppiness(highs, lows, closes, settings.choppiness_period)
    if chop is not None:
        scored.append(("choppiness", chop, score_choppiness(chop)))
    return scored
