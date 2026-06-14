"""Volume/event scoring rules and their composite contribution.

Agent: analyst
Role: map OBV / golden cross / RSI-2 to 0-100 sub-scores.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.domain import indicators, indicators_event

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings

# Fixed band cut-points from the sprint spec (the rule itself, not tunable policy);
# named module constants mirroring ``technical_rules_range.py``. Boundaries use
# strict ``>`` / ``<`` so a value equal to a cut-point falls into the lower band.
_OBV_SCORES = (70.0, 35.0)
_GOLDEN_SCORES = (75.0, 25.0)
_RSI2_OVERSOLD, _RSI2_OVERBOUGHT = 10.0, 90.0
_RSI2_SCORES = (80.0, 20.0)
_NEUTRAL = 50.0


def score_obv(obv_value: float, signal: float) -> float:
    """OBV above its signal reads as accumulation (bullish); below as distribution."""
    if obv_value > signal:
        return _OBV_SCORES[0]
    return _OBV_SCORES[1]


def score_golden_cross(is_golden: bool) -> float:
    """A golden cross (short SMA over long SMA) is bullish; the reverse is bearish."""
    if is_golden:
        return _GOLDEN_SCORES[0]
    return _GOLDEN_SCORES[1]


def score_rsi2(value: float) -> float:
    """Deep oversold is a mean-reversion buy; overbought is bearish; else neutral."""
    if value < _RSI2_OVERSOLD:
        return _RSI2_SCORES[0]
    if value > _RSI2_OVERBOUGHT:
        return _RSI2_SCORES[1]
    return _NEUTRAL


def event_indicator_scores(
    closes: list[float], volumes: list[float], settings: AnalystSettings
) -> list[tuple[str, float, float]]:
    """Compute and score every volume/event indicator with enough history; skip rest."""
    scored: list[tuple[str, float, float]] = []
    obv = indicators_event.obv(closes, volumes, settings.obv_signal_period)
    if obv is not None:
        scored.append(("obv", obv[0], score_obv(obv[0], obv[1])))
    is_golden = indicators_event.golden_cross(
        closes, settings.golden_cross_short_period, settings.sma_long_period
    )
    if is_golden is not None:
        value = 1.0 if is_golden else 0.0
        scored.append(("golden_cross", value, score_golden_cross(is_golden)))
    rsi2 = indicators.rsi(closes, settings.rsi2_period)
    if rsi2 is not None:
        scored.append(("rsi2", rsi2, score_rsi2(rsi2)))
    return scored
