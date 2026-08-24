"""Committed news-fixture sentiment measurement tests.

Agent: analyst
Role: prove S186 reproduces the measured batch-level sentiment shift.
External I/O: none.
"""

from __future__ import annotations

import collections
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest

from agents.analyst.domain import analyze
from agents.analyst.domain.scoring import ScoreBreakdown
from agents.analyst.domain.sentiment_rules import score_sentiment
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import candidate, candidate_set
from contracts.common import Provenance
from contracts.provider import DataQualityTrace, MarketData, RegimeContext
from kernel import CollectingFaultSink

if TYPE_CHECKING:
    from collections.abc import Mapping


_FIXTURE = Path(__file__).parent / "data" / "news_sched_2026_08_21.json"


def _fixture() -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(_FIXTURE.read_text(encoding="utf-8")))


def _confidence(
    *,
    technical: float,
    fundamental: float | None,
    sentiment: float | None,
    settings: AnalystSettings,
) -> float:
    weighted = settings.technical_weight * technical
    weight_sum = settings.technical_weight
    if fundamental is not None:
        weighted += settings.fundamental_weight * fundamental
        weight_sum += settings.fundamental_weight
    if sentiment is not None:
        weighted += settings.sentiment_weight * sentiment
        weight_sum += settings.sentiment_weight
    composite = weighted / weight_sum
    return settings.confidence_floor + composite * settings.confidence_span


def _regime() -> RegimeContext:
    return RegimeContext(
        label="risk_on",
        vix=12.0,
        as_of=datetime(2026, 8, 21, 22, 30, tzinfo=UTC),
        base_min_confidence=0.60,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="sched-2026-08-21", source_agent="provider"),
    )


def _market(news: dict[str, Any]) -> MarketData:
    return MarketData(
        bars=(),
        news={ticker: tuple(headlines) for ticker, headlines in news.items()},
        quality=DataQualityTrace(requested=len(news), returned=len(news)),
        provenance=Provenance(run_id="sched-2026-08-21", source_agent="provider"),
    )


def test_sched_2026_08_21_fixture_reproduces_weighted_measurement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ANLZ-IDM-01 / ANLZ-NEV-03: the fixture reproduces the KO floor crossing."""
    data = _fixture()
    settings = AnalystSettings()
    baseline = data["baseline"]
    confidences: dict[str, float] = {}
    sentiments_lost: collections.Counter[str] = collections.Counter()

    def score_one(
        scored_candidate: Any,
        _bars: tuple[Any, ...],
        _fundamentals: dict[str, float],
        _benchmark_bars: tuple[Any, ...],
        news: tuple[str, ...],
        _settings: AnalystSettings,
        *,
        headline_weights: Mapping[str, float],
        alpha_score: float | None = None,
    ) -> ScoreBreakdown:
        ticker = scored_candidate.ticker
        raw_sentiment, metrics = score_sentiment(
            news, headline_weights=headline_weights
        )
        if raw_sentiment is None and "sentiment_score" in baseline[ticker]:
            sentiments_lost[ticker] += 1
        sentiment = None if raw_sentiment is None else raw_sentiment / 100.0
        confidence = _confidence(
            technical=baseline[ticker]["technical_score"],
            fundamental=baseline[ticker].get("fundamental_score"),
            sentiment=sentiment,
            settings=settings,
        )
        confidences[ticker] = confidence
        return ScoreBreakdown(
            technical_score=baseline[ticker]["technical_score"],
            confidence=confidence,
            metrics=metrics,
            fundamental_score=baseline[ticker].get("fundamental_score"),
            sentiment_score=sentiment,
            alpha158_score=alpha_score,
        )

    monkeypatch.setattr(analyze, "score_candidate", score_one)
    result = analyze.score_candidates(
        candidate_set(*(candidate(ticker) for ticker in baseline)),
        _market(data["news"]),
        _regime(),
        (),
        settings,
        CollectingFaultSink(),
    )

    assert result is not None
    assert baseline["KO"]["confidence"] == pytest.approx(0.605, abs=0.0005)
    assert confidences["KO"] == pytest.approx(0.599, abs=0.0005)
    assert sentiments_lost == {}
