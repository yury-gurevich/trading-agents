"""Batch-duplicate sentiment weighting tests.

Agent: analyst
Role: prove repeated market-wide headlines carry fractional sentiment weight.
External I/O: none.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from agents.analyst.domain.sentiment_rules import score_sentiment
from agents.analyst.domain.sentiment_weights import batch_headline_weights

_FIXTURE = Path(__file__).parent / "data" / "news_sched_2026_08_21.json"


def _fixture() -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(_FIXTURE.read_text(encoding="utf-8")))


def test_shared_headline_is_fractional_in_weighted_mean() -> None:
    """ANLZ-IDM-01 / ANLZ-OBS-04: duplicated headlines carry 1/n weight."""
    shared = "Loss widens as lawsuit and fraud probe deepen"
    exclusive = "Profit surges to record as sales beat"
    weights = batch_headline_weights(
        {
            "AAA": (shared, exclusive),
            "BBB": (shared,),
        }
    )

    score, metrics = score_sentiment(
        (shared, exclusive),
        headline_weights=weights,
    )

    assert score == pytest.approx((0.0 * 0.5 + 100.0) / 1.5)
    assert metrics["sentiment_articles"] == 2.0
    assert metrics["sentiment_batch_weighted_articles"] == pytest.approx(1.5)


def test_all_heavily_shared_headlines_still_score() -> None:
    """ANLZ-IDM-01: a tiny positive denominator is still a real denominator."""
    score, metrics = score_sentiment(
        (
            "Profit surges to record as sales beat",
            "Loss widens as lawsuit and fraud probe deepen",
        ),
        headline_weights={
            "Profit surges to record as sales beat": 0.1,
            "Loss widens as lawsuit and fraud probe deepen": 0.1,
        },
    )

    assert score == pytest.approx(50.0)
    assert metrics["sentiment_batch_weighted_articles"] == pytest.approx(0.2)


def test_fixture_exclusive_news_tickers_are_unchanged() -> None:
    """ANLZ-IDM-01: exclusive fixture headlines remain byte-identical."""
    data = _fixture()
    weights = batch_headline_weights(data["news"])

    for ticker in ("DUK", "GILD", "MET", "TGT"):
        unweighted_score, unweighted_metrics = score_sentiment(
            tuple(data["news"][ticker])
        )
        weighted_score, weighted_metrics = score_sentiment(
            tuple(data["news"][ticker]),
            headline_weights=weights,
        )

        assert weighted_score == unweighted_score
        if not unweighted_metrics:
            assert weighted_metrics == {}
        else:
            assert (
                weighted_metrics["sentiment_articles"]
                == unweighted_metrics["sentiment_articles"]
            )
            assert weighted_metrics[
                "sentiment_batch_weighted_articles"
            ] == pytest.approx(unweighted_metrics["sentiment_articles"])


def test_neutral_headline_is_skipped_before_weighting() -> None:
    """ANLZ-IDM-01: no-lexicon headlines are skipped, not diluted."""
    score, metrics = score_sentiment(
        (
            "Company schedules its annual shareholder meeting",
            "Sales beat estimates",
        ),
        headline_weights={
            "Company schedules its annual shareholder meeting": 0.1,
            "Sales beat estimates": 0.5,
        },
    )

    assert score == pytest.approx(100.0)
    assert metrics["sentiment_articles"] == 1.0
    assert metrics["sentiment_batch_weighted_articles"] == pytest.approx(0.5)


def test_weighted_article_metric_names_unit_and_batch_scope() -> None:
    """ANLZ-OBS-04 / DL-112: sentiment metric names distinguish units."""
    _, metrics = score_sentiment(
        ("Profit surges to record as sales beat",),
        headline_weights={"Profit surges to record as sales beat": 0.25},
    )

    assert metrics["sentiment_articles"] == 1.0
    assert metrics["sentiment_batch_weighted_articles"] == pytest.approx(0.25)
    assert "sentiment_weighted_articles" not in metrics
    assert "sentiment_positive" not in metrics
    assert "sentiment_negative" not in metrics
