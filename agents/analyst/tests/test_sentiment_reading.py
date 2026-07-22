"""Sentiment-reading construction and persistence tests.

Agent: analyst
Role: verify the lexicon (champion) and provider (shadow challenger) readings are
built from their sources and persisted per run + ticker (including non-recommended
tickers), linked to the run; the provider reading never gates a decision.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import ScoreBreakdown
from agents.analyst.domain.sentiment_reading import (
    LEXICON_SCORER,
    PROVIDER_SCORER,
    SentimentReading,
    lexicon_reading,
    provider_reading,
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
from contracts.common import Provenance
from contracts.provider import RegimeContext
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


def test_decide_preserves_sentiment_reading_on_rejections() -> None:
    """Kills recommend.x_decide__mutmut_8 and x_decide__mutmut_18."""
    score = ScoreBreakdown(
        technical_score=0.5,
        confidence=0.0,
        metrics={"sentiment_articles": 1.0, "sentiment_positive": 1.0},
        sentiment_score=1.0,
        rejection_reason="insufficient_market_history",
    )
    regime = RegimeContext(
        label="risk_on",
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.6,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime-fixture", source_agent="provider"),
    )

    decision = decide(candidate(), score, regime)

    assert decision.rejection == Rejection(
        ticker="AAPL", reason="insufficient_market_history"
    )
    assert decision.sentiment_reading == SentimentReading(
        "AAPL", "lexicon", 1.0, 1, 1, 0
    )
    floor_score = ScoreBreakdown(
        technical_score=0.5,
        confidence=0.5,
        metrics={"sentiment_articles": 1.0, "sentiment_positive": 1.0},
        sentiment_score=1.0,
    )
    floor_decision = decide(candidate(), floor_score, regime)
    assert floor_decision.rejection is not None
    assert floor_decision.sentiment_reading == decision.sentiment_reading


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


def test_provider_reading_from_a_vendor_score() -> None:
    reading = provider_reading("AAPL", 0.58)
    assert reading.ticker == "AAPL"
    assert reading.scorer == PROVIDER_SCORER
    assert reading.score == 0.58
    assert (reading.articles, reading.positive, reading.negative) == (0, 0, 0)


def test_analyze_persists_provider_sentiment_reading_node() -> None:
    scan = candidate_set(candidate())
    bus, graph, sink = wire_analyst(source_bars=bars(), sentiment={"AAPL": 0.58})

    response = bus.request(analyze_message(scan))

    run_id = response.payload["run_id"]
    node = graph.get_node("SentimentReading", f"{run_id}:provider:AAPL")
    assert node is not None
    assert node.props["score"] == 0.58
    assert node.props["scorer"] == "provider"
    # No news, so the lexicon scorer produced nothing: the two scorers are independent.
    assert graph.get_node("SentimentReading", f"{run_id}:lexicon:AAPL") is None
    assert sink.faults == []


def test_analyze_aligns_both_scorer_readings_for_one_run() -> None:
    scan = candidate_set(candidate())
    bus, graph, sink = wire_analyst(
        source_bars=bars(),
        news={"AAPL": ("Profit surges to record as sales beat",)},
        sentiment={"AAPL": 0.58},
    )

    response = bus.request(analyze_message(scan))

    run_id = response.payload["run_id"]
    assert graph.get_node("SentimentReading", f"{run_id}:lexicon:AAPL") is not None
    assert graph.get_node("SentimentReading", f"{run_id}:provider:AAPL") is not None
    assert sink.faults == []


def test_provider_sentiment_does_not_gate_the_recommendation() -> None:
    scan = candidate_set(candidate())
    bus_a, _, _ = wire_analyst(source_bars=bars())
    bus_b, _, _ = wire_analyst(source_bars=bars(), sentiment={"AAPL": 0.58})

    baseline = bus_a.request(analyze_message(scan)).payload["recommendations"]
    shadowed = bus_b.request(analyze_message(scan)).payload["recommendations"]

    assert baseline  # AAPL was recommended, so there is a confidence to compare
    assert [r["confidence"] for r in shadowed] == [r["confidence"] for r in baseline]
