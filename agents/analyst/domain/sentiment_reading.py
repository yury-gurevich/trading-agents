"""Persisted sentiment reading — one scorer's net-tone result for a ticker.

Agent: analyst
Role: capture a scorer's sentiment reading (aligned per run + ticker, incl.
non-recommended tickers) for the champion-challenger scorecard.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.analyst.domain.scoring import ScoreBreakdown

LEXICON_SCORER = "lexicon"


@dataclass(frozen=True)
class SentimentReading:
    """One scorer's 0-1 sentiment reading for a ticker in an analyst run."""

    ticker: str
    scorer: str
    score: float
    articles: int
    positive: int
    negative: int


def lexicon_reading(ticker: str, score: ScoreBreakdown) -> SentimentReading | None:
    """Build the champion (lexicon) reading from a score, or None when absent."""
    if score.sentiment_score is None:
        return None
    metrics = score.metrics
    return SentimentReading(
        ticker=ticker,
        scorer=LEXICON_SCORER,
        score=score.sentiment_score,
        articles=int(metrics.get("sentiment_articles", 0.0)),
        positive=int(metrics.get("sentiment_positive", 0.0)),
        negative=int(metrics.get("sentiment_negative", 0.0)),
    )
