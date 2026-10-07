"""Synthetic scoring inputs shared by S255's source pins.

Agent: testing
Role: build actual analyst outputs under default and moved settings.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from tests.score_arithmetic_support import recorded_order

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import ScoreBreakdown, score_candidate
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import candidate
from contracts.provider import OHLCVBar

if TYPE_CHECKING:
    from contracts.analyst import Recommendation

MOVED = {
    "technical_weight": 0.40,
    "fundamental_weight": 0.35,
    "sentiment_weight": 0.25,
    "alpha158_pillar_weight": 0.15,
    "relative_strength_weight": 0.30,
    "confidence_floor": 0.25,
    "confidence_span": 0.65,
}
FUNDAMENTALS = {
    "peBasicExclExtraTTM": 18.0,
    "roeTTM": 18.0,
    "netProfitMarginTTM": 15.0,
    "currentRatioQuarterly": 1.4,
    "pbQuarterly": 2.0,
    "totalDebt/totalEquityQuarterly": 0.4,
    "epsGrowthTTMYoy": 12.0,
    "revenueGrowthTTMYoy": 10.0,
}
NEWS = (
    "Profit and revenue beat estimates with strong growth",
    "Guidance misses estimates",
)


def settings(moved: bool = False) -> AnalystSettings:
    """Move every recorded constant, including the inactive alpha weight."""
    return AnalystSettings(**MOVED) if moved else AnalystSettings()


def bars(ticker: str = "AAPL") -> tuple[OHLCVBar, ...]:
    """Two hundred fifty dated bars make the technical mean and RS measurable."""
    result = []
    for offset in range(250):
        close = 100.0 + offset * 0.03 + (offset % 11 - 5) * 0.9
        result.append(
            OHLCVBar(
                ticker=ticker,
                bar_date=date(2025, 1, 1) + timedelta(days=offset),
                open=close - 0.2,
                high=close + 1.5,
                low=close - 1.5,
                close=close,
                volume=1_000_000 + offset * 500,
            )
        )
    return tuple(result)


def scored_order(
    config: AnalystSettings, absent: str = "none"
) -> tuple[ScoreBreakdown, Recommendation]:
    """Score with real rules, then construct a held recommendation unchanged."""
    score = score_candidate(
        candidate(),
        bars(),
        {} if absent in {"fundamental", "both"} else FUNDAMENTALS,
        bars("SPY"),
        () if absent in {"sentiment", "both"} else NEWS,
        config,
    )
    _, regime = recorded_order()
    decision = decide(candidate(), score, regime, held=True, settings=config)
    assert decision.recommendation is not None
    return score, decision.recommendation
