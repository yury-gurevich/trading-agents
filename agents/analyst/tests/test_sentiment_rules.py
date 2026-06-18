"""Sentiment-lexicon scoring tests.

Agent: analyst
Role: verify the Loughran-McDonald net-tone scorer over news headlines.
External I/O: none.
"""

from __future__ import annotations

import pytest

from agents.analyst.domain.sentiment_rules import (
    _NEGATIVE,
    _POSITIVE,
    score_sentiment,
)


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


def test_lm_only_positive_words_score_positive() -> None:
    # 'excellent'/'innovative' are LM master-dictionary positives the curated
    # headline list never had -> the dictionary upgrade now scores them.
    score, metrics = score_sentiment(("Firm reports excellent and innovative results",))
    assert score == pytest.approx(100.0)
    assert metrics["sentiment_positive"] == 2.0


def test_lm_only_negative_words_score_negative() -> None:
    score, metrics = score_sentiment(
        ("Auditor flags fraudulent and adverse accounting",)
    )
    assert score == pytest.approx(0.0)
    assert metrics["sentiment_negative"] == 2.0


def test_lm_master_dictionary_and_headline_terms_loaded() -> None:
    # full LM master dictionary (Positive 354, Negative 2355) unioned with the
    # curated headline terms -> each source's exclusive words are all present.
    assert len(_POSITIVE) >= 354
    assert len(_NEGATIVE) >= 2355
    assert {"excellent", "innovative", "achieve"} <= _POSITIVE  # LM-only
    assert {"fraudulent", "adverse", "abandon"} <= _NEGATIVE  # LM-only
    assert {"beat", "surge", "profit"} <= _POSITIVE  # headline-only
    assert {"plunge", "tumble", "miss"} <= _NEGATIVE  # headline-only


def test_positive_and_negative_lexicons_are_disjoint() -> None:
    # the union needs no conflict resolution only because the two sources never
    # disagree on polarity; guard that invariant against future LM refreshes.
    assert _POSITIVE.isdisjoint(_NEGATIVE)
