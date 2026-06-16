"""Sentiment-lexicon scoring tests.

Agent: analyst
Role: verify the Loughran-McDonald net-tone scorer over news headlines.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.analyst.domain.sentiment_rules import score_sentiment


def test_all_positive_headline_scores_100() -> None:
    score, metrics = score_sentiment(("Profit surges to record as sales beat",))
    assert score == pytest.approx(100.0)
    assert metrics == {
        "sentiment_articles": 1.0,
        "sentiment_positive": 4.0,
        "sentiment_negative": 0.0,
    }


def test_all_negative_headline_scores_0() -> None:
    score, _ = score_sentiment(("Loss widens as lawsuit and fraud probe deepen",))
    assert score == pytest.approx(0.0)


def test_balanced_headline_scores_50() -> None:
    score, metrics = score_sentiment(("Profit gains offset by loss warning",))
    assert score == pytest.approx(50.0)
    assert metrics["sentiment_positive"] == 2.0
    assert metrics["sentiment_negative"] == 2.0


def test_headline_without_lexicon_word_is_skipped() -> None:
    score, metrics = score_sentiment(
        ("Company schedules its annual shareholder meeting", "Sales beat estimates")
    )
    assert score == pytest.approx(100.0)
    assert metrics["sentiment_articles"] == 1.0


def test_all_neutral_or_empty_returns_none() -> None:
    assert score_sentiment(()) == (None, {})
    assert score_sentiment(("Board appoints a new regional director",)) == (None, {})


def test_mixed_headlines_average_only_the_scored() -> None:
    score, metrics = score_sentiment(
        (
            "Profit surges to record as sales beat",
            "Company updates its corporate logo",
            "Loss widens as lawsuit and fraud probe deepen",
        )
    )
    assert score == pytest.approx(50.0)
    assert metrics["sentiment_articles"] == 2.0
    assert metrics["sentiment_positive"] == 4.0
    assert metrics["sentiment_negative"] == 4.0


def test_case_insensitive_and_punctuation_tokenised() -> None:
    score, _ = score_sentiment(("PROFIT SURGES, RECORD BEAT!",))
    assert score == pytest.approx(100.0)
