"""Own-company headline sentiment proofs.

Agent: analyst
Role: prove ANLZ-OUT-11's subject filter, minimum, counts and scorer wiring.
External I/O: local bundled company table and fleet universe text only.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.analyst.domain.scoring import score_candidate
from agents.analyst.domain.sentiment_rules import score_sentiment
from agents.analyst.domain.sentiment_subject import (
    COMPANY_NAMES,
    own_headlines,
    subject_sentiment,
)
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import bar, candidate


@pytest.mark.parametrize(
    ("ticker", "headline", "expected"),
    [
        ("MRK", "Merck's profit rises", True),
        ("MRK", "Merck, shares fall", True),
        ("MRK", "Mercker profit rises", False),
        ("MRK", "$MRK falls", True),
        ("MRK", "Shares (MRK) fall", True),
        ("MRK", "NYSE:MRK falls", True),
        ("MRK", "NYSE: MRK falls", True),
        ("MRK", "Vaxcyte vaccine trial succeeds", False),
        ("MRK", "MRK falls", False),
        ("MRK", "Vaxcyte Takes Aim at Pfizer and Merck", True),
        ("IBM", "IBM profit rises", True),
        ("GE", "GE Vernova profit rises", False),
        ("GE", "GE Aerospace profit rises", True),
        ("TGT", "Target cuts outlook", True),
        ("TGT", "Raises Price Target On Nike", False),
        ("TGT", "Raises price Target for Walmart", False),
        ("META", "Metaverse profit rises", False),
        ("MMM", "Company raises $3M", False),
        ("MRK", "merck profit rises", False),
        ("MRK", "SuperMerck profit rises", False),
    ],
)
def test_a_headline_is_own_only_when_it_names_the_company(
    ticker: str, headline: str, expected: bool
) -> None:
    """ANLZ-OUT-11: names at word edges or marked tickers count, whoever the subject."""
    assert own_headlines(ticker, (headline,)) == ((headline,) if expected else ())


def test_another_companys_news_does_not_move_the_score() -> None:
    """ANLZ-OUT-11: the score and article metrics use only the two own headlines."""
    own = ("Merck profit", "Merck loss")
    news = (*own, "Vaxcyte loss", "Wall Street falls")
    expected, metrics = score_sentiment(own)
    score, actual = subject_sentiment("MRK", news, 2)

    assert score == expected == 50.0
    assert actual == {
        **metrics,
        "sentiment_served_headlines": 4.0,
        "sentiment_own_headlines": 2.0,
        "sentiment_subject_filtered": 1.0,
    }
    assert actual["sentiment_articles"] == 2.0


def test_fewer_own_scored_headlines_than_the_minimum_is_no_pillar() -> None:
    """ANLZ-OUT-11: two own headlines with only one lexicon-bearing one miss two."""
    news = (
        "Merck profit",
        "Merck schedules its annual shareholder meeting",
        "Vaxcyte profit",
        "Wall Street loss",
    )
    counts = {
        "sentiment_served_headlines": 4.0,
        "sentiment_own_headlines": 2.0,
        "sentiment_subject_filtered": 1.0,
    }
    assert subject_sentiment("MRK", news, 2) == (None, counts)
    score, metrics = subject_sentiment("MRK", news, 1)
    assert score == 100.0
    assert metrics["sentiment_articles"] == 1.0
    assert metrics.items() >= counts.items()


def test_the_minimum_counts_scored_headlines_with_their_weights() -> None:
    """ANLZ-OUT-11 / ANLZ-OBS-04: two scored headlines pass at weighted size 1.5."""
    own = ("Merck profit", "Merck loss")
    score, metrics = subject_sentiment("MRK", own, 2, headline_weights={own[0]: 0.5})
    assert score == pytest.approx(100.0 * 0.5 / 1.5)
    assert metrics["sentiment_articles"] == 2.0
    assert metrics["sentiment_batch_weighted_articles"] == 1.5


def test_a_ticker_the_table_does_not_list_scores_every_headline() -> None:
    """ANLZ-OUT-11: an unlisted ticker scores both headlines even at minimum three."""
    news = ("Merck profit", "Vaxcyte loss")
    expected, metrics = score_sentiment(news)
    assert own_headlines("ZZZZ", news) is None
    assert subject_sentiment("ZZZZ", news, 3) == (
        expected,
        {
            **metrics,
            "sentiment_served_headlines": 2.0,
            "sentiment_own_headlines": 2.0,
            "sentiment_subject_filtered": 0.0,
        },
    )
    assert expected == 50.0


def test_no_served_news_is_no_pillar_and_no_metrics() -> None:
    """ANLZ-OUT-11: no served news differs from served news with zero own headlines."""
    assert subject_sentiment("MRK", (), 2) == (None, {})
    assert subject_sentiment("MRK", ("Vaxcyte profit", "Wall Street loss"), 2) == (
        None,
        {
            "sentiment_served_headlines": 2.0,
            "sentiment_own_headlines": 0.0,
            "sentiment_subject_filtered": 1.0,
        },
    )


def test_every_ticker_of_the_fleets_universe_is_in_the_company_table() -> None:
    """ANLZ-OUT-11: all 99 universe tickers have nonempty bundled company names."""
    path = Path(__file__).resolve().parents[3] / "scripts" / "universe_sp100.txt"
    universe = {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert len(universe) == 99
    assert set(COMPANY_NAMES) == universe
    assert all(COMPANY_NAMES[ticker] for ticker in universe)
    assert all(name.strip() for names in COMPANY_NAMES.values() for name in names)


def test_the_minimum_is_a_bounded_tunable_defaulting_to_two() -> None:
    """ANLZ-OUT-11: default two, minimum one, and values outside 1..10 are refused."""
    assert AnalystSettings().sentiment_min_own_headlines == 2
    assert (
        AnalystSettings(sentiment_min_own_headlines=1).sentiment_min_own_headlines == 1
    )
    field = AnalystSettings.model_fields["sentiment_min_own_headlines"]
    assert field.description
    assert "DL-308" in field.description
    for value in (0, 11):
        with pytest.raises(ValidationError, match="sentiment_min_own_headlines"):
            AnalystSettings(sentiment_min_own_headlines=value)


def test_the_scorer_reads_own_headlines_by_its_settings_and_weights() -> None:
    """ANLZ-OUT-11: score_candidate threads ticker, configured minimum and weights."""
    own = ("Apple profit", "iPhone loss", "Apple record profit")
    news = (*own, "Microsoft profit", "Markets fall")
    weights = {own[1]: 0.5}
    rows = (bar("AAPL", 1, 100.0), bar("AAPL", 0, 101.0))
    settings = AnalystSettings()
    score = score_candidate(
        candidate(), rows, {}, (), news, settings, headline_weights=weights
    )
    assert score.sentiment_score == pytest.approx(0.8)
    assert score.metrics["sentiment_own_headlines"] == 3.0
    assert score.metrics["sentiment_served_headlines"] == 5.0
    assert score.metrics["sentiment_articles"] == 3.0
    assert score.metrics["sentiment_batch_weighted_articles"] == 2.5
    absent = score_candidate(
        candidate(),
        rows,
        {},
        (),
        news,
        AnalystSettings(sentiment_min_own_headlines=4),
        headline_weights=weights,
    )
    assert absent.sentiment_score is None
    assert absent.metrics["composite_score"] == absent.technical_score
