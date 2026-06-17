"""Sentiment-reading construction and persistence tests.

Agent: analyst
Role: verify the lexicon reading is built from a score and persisted per run +
ticker (including non-recommended tickers), linked to the run.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.domain.scoring import ScoreBreakdown
from agents.analyst.domain.sentiment_reading import (
    LEXICON_SCORER,
    SentimentReading,
    lexicon_reading,
)
from agents.analyst.store import write_analysis
from agents.analyst.tests.helpers import (
    analyze_message,
    bars,
    candidate,
    candidate_set,
    wire_analyst,
)
from contracts.analyst import Rejection
from kernel import InMemoryGraphStore


def test_lexicon_reading_from_a_scored_candidate() -> None:
    score = ScoreBreakdown(
        technical_score=0.5,
        confidence=0.6,
        metrics={
            "sentiment_articles": 2.0,
            "sentiment_positive": 3.0,
            "sentiment_negative": 1.0,
        },
        sentiment_score=0.75,
    )
    reading = lexicon_reading("AAPL", score)
    assert reading is not None
    assert reading.ticker == "AAPL"
    assert reading.scorer == LEXICON_SCORER
    assert reading.score == 0.75
    assert (reading.articles, reading.positive, reading.negative) == (2, 3, 1)


def test_lexicon_reading_is_none_without_sentiment() -> None:
    score = ScoreBreakdown(technical_score=0.5, confidence=0.6, metrics={})
    assert lexicon_reading("AAPL", score) is None


def test_write_analysis_persists_reading_for_a_rejected_ticker() -> None:
    graph = InMemoryGraphStore()
    reading = SentimentReading(
        ticker="AAPL", scorer="lexicon", score=0.75, articles=2, positive=3, negative=1
    )

    provenance = write_analysis(
        graph,
        candidate_set=candidate_set(candidate()),
        recommendations=(),  # AAPL was scored but NOT recommended
        rejections=(Rejection(ticker="AAPL", reason="confidence below floor"),),
        sentiment_readings=(reading,),
    )

    node = graph.get_node("SentimentReading", f"{provenance.run_id}:lexicon:AAPL")
    assert node is not None
    assert node.props["score"] == 0.75
    assert node.props["scorer"] == "lexicon"
    assert node.props["positive"] == 3.0
    assert node.props["source_run_id"] == provenance.run_id
    run = graph.get_node("AnalystRun", provenance.run_id)
    assert run is not None
    labels = [n.label for n in graph.descendants(run, max_depth=1)]
    assert labels == ["SentimentReading"]


def test_analyze_persists_sentiment_reading_node() -> None:
    scan = candidate_set(candidate())
    bus, graph, sink = wire_analyst(
        source_bars=bars(),
        news={"AAPL": ("Profit surges to record as sales beat",)},
    )

    response = bus.request(analyze_message(scan))

    run_id = response.payload["run_id"]
    node = graph.get_node("SentimentReading", f"{run_id}:lexicon:AAPL")
    assert node is not None
    assert node.props["score"] == 1.0
    assert node.props["scorer"] == "lexicon"
    assert sink.faults == []
