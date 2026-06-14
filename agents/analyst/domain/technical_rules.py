"""Indicator scoring rules and the technical composite.

Agent: analyst
Role: map indicator values to 0-100 sub-scores and average the available ones.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.domain import indicators
from agents.analyst.domain.technical_rules_range import range_indicator_scores

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings
    from contracts.provider import OHLCVBar

# Fixed scoring rule from the sprint spec: band cut-points and the 0-100 sub-score
# each band emits. These define the rule itself (not operator-tunable policy), so
# they are named module constants rather than settings. Boundaries use ``<`` so a
# value equal to a cut-point falls into the next (higher) band.
_RSI_OVERSOLD, _RSI_NEUTRAL_LOW, _RSI_OVERBOUGHT = 30.0, 50.0, 70.0
_RSI_SCORES = (80.0, 65.0, 50.0, 25.0)
_MACD_SCORES = (75.0, 60.0, 25.0, 45.0)
_BB_LOWER, _BB_UPPER = 0.30, 0.70
_BB_SCORES = (75.0, 50.0, 30.0)
_SMA_FAR_ABOVE, _SMA_ABOVE, _SMA_BELOW = 5.0, 0.0, -5.0
_SMA_SCORES = (75.0, 60.0, 40.0, 20.0)
_EMA_FAR_ABOVE, _EMA_ABOVE, _EMA_BELOW = 1.0, 0.0, -1.0
_EMA_SCORES = (75.0, 60.0, 40.0, 25.0)
_NEUTRAL = 50.0


def score_rsi(value: float) -> float:
    """Lower RSI is more bullish: oversold scores high, overbought scores low."""
    if value < _RSI_OVERSOLD:
        return _RSI_SCORES[0]
    if value < _RSI_NEUTRAL_LOW:
        return _RSI_SCORES[1]
    if value < _RSI_OVERBOUGHT:
        return _RSI_SCORES[2]
    return _RSI_SCORES[3]


def score_macd(line: float, histogram: float) -> float:
    """Positive line and rising histogram is most bullish."""
    if line > 0.0 and histogram > 0.0:
        return _MACD_SCORES[0]
    if histogram > 0.0:
        return _MACD_SCORES[1]
    if line < 0.0 and histogram < 0.0:
        return _MACD_SCORES[2]
    return _MACD_SCORES[3]


def score_bollinger(position: float) -> float:
    """Near the lower band is bullish; near the upper band is bearish."""
    if position < _BB_LOWER:
        return _BB_SCORES[0]
    if position < _BB_UPPER:
        return _BB_SCORES[1]
    return _BB_SCORES[2]


def score_sma_distance(distance_pct: float) -> float:
    """Trading further above the SMA200 is more bullish."""
    if distance_pct > _SMA_FAR_ABOVE:
        return _SMA_SCORES[0]
    if distance_pct > _SMA_ABOVE:
        return _SMA_SCORES[1]
    if distance_pct > _SMA_BELOW:
        return _SMA_SCORES[2]
    return _SMA_SCORES[3]


def score_ema_crossover(spread_pct: float) -> float:
    """A wider positive short-over-long EMA spread is more bullish."""
    if spread_pct > _EMA_FAR_ABOVE:
        return _EMA_SCORES[0]
    if spread_pct > _EMA_ABOVE:
        return _EMA_SCORES[1]
    if spread_pct > _EMA_BELOW:
        return _EMA_SCORES[2]
    return _EMA_SCORES[3]


def score_technical(
    bars: list[OHLCVBar], settings: AnalystSettings
) -> tuple[float, dict[str, float]]:
    """Average the available indicator sub-scores; neutral 50 when none compute.

    ``bars`` must be sorted ascending by ``bar_date`` (the caller guarantees this).
    Momentum/trend sub-scores (over closes) and range sub-scores (over high/low/
    close) are pooled before averaging.
    """
    closes = [bar.close for bar in bars]
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    metrics: dict[str, float] = {}
    sub_scores: list[float] = []
    triples = _momentum_scores(closes, settings) + range_indicator_scores(
        highs, lows, closes, settings
    )
    for name, value, score in triples:
        metrics[name], metrics[f"{name}_score"] = value, score
        sub_scores.append(score)
    if not sub_scores:
        return _NEUTRAL, {"indicators_available": 0.0}
    metrics["indicators_available"] = float(len(sub_scores))
    return sum(sub_scores) / len(sub_scores), metrics


def _momentum_scores(
    closes: list[float], settings: AnalystSettings
) -> list[tuple[str, float, float]]:
    """Compute and score every momentum/trend indicator with enough history."""
    rsi = indicators.rsi(closes, settings.rsi_period)
    bb = indicators.bollinger_position(
        closes, settings.bollinger_window, settings.bollinger_sigma
    )
    sma = indicators.sma_distance(closes, settings.sma_long_period)
    ema = indicators.ema_crossover_spread(
        closes, settings.ema_short_period, settings.ema_long_period
    )
    macd = indicators.macd(
        closes, settings.macd_fast, settings.macd_slow, settings.macd_signal
    )
    scored: list[tuple[str, float, float]] = []
    if rsi is not None:
        scored.append(("rsi", rsi, score_rsi(rsi)))
    if macd is not None:
        scored.append(("macd_histogram", macd[2], score_macd(macd[0], macd[2])))
    if bb is not None:
        scored.append(("bollinger_position", bb, score_bollinger(bb)))
    if sma is not None:
        scored.append(("sma_distance_pct", sma, score_sma_distance(sma)))
    if ema is not None:
        scored.append(("ema_spread_pct", ema, score_ema_crossover(ema)))
    return scored
