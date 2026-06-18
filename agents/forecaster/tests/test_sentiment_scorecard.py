"""Sentiment-scorecard capability tests (graph alignment + never-promotes).

Agent: forecaster
Role: verify the forecaster reads the three scorers' readings, aligns complete
      cases against injected forward returns, and never promotes.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.forecaster.tests.helpers import (
    seed_finbert,
    seed_reading,
    sentiment_scorecard_message,
    wire_forecaster,
)
from contracts.forecaster import Scorecard

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore

MODEL = "finbert-sentiment"


def _seed_complete(
    graph: InMemoryGraphStore,
    run: str,
    ticker: str,
    lex: float,
    prov: float,
    fin: float,
) -> None:
    seed_reading(graph, run_id=run, ticker=ticker, scorer="lexicon", score=lex)
    seed_reading(graph, run_id=run, ticker=ticker, scorer="provider", score=prov)
    seed_finbert(graph, model_id=MODEL, ref=f"{run}:{ticker}", value=fin)


def test_sentiment_scorecard_aligns_complete_cases_and_never_promotes() -> None:
    bus, graph, _sink = wire_forecaster(news={})
    _seed_complete(graph, "run1", "AAPL", 0.8, 0.7, 0.90)
    _seed_complete(graph, "run1", "MSFT", 0.4, 0.5, 0.30)
    _seed_complete(graph, "run1", "NVDA", 0.6, 0.6, 0.65)
    returns = {"run1:AAPL": 0.05, "run1:MSFT": -0.02, "run1:NVDA": 0.03}

    card = Scorecard.model_validate(
        bus.request(sentiment_scorecard_message(MODEL, returns)).payload
    )

    assert card.promotion_eligible is False
    assert card.sample_size == 3
    assert card.metrics["complete_cases"] == 3.0
    assert "ic_finbert" in card.metrics


def test_incomplete_refs_and_other_models_are_skipped() -> None:
    bus, graph, _sink = wire_forecaster(news={})
    _seed_complete(graph, "r", "AAPL", 0.8, 0.7, 0.9)  # complete -> kept
    # missing provider:
    seed_reading(graph, run_id="r", ticker="MSFT", scorer="lexicon", score=0.4)
    seed_finbert(graph, model_id=MODEL, ref="r:MSFT", value=0.3)
    # missing finbert:
    seed_reading(graph, run_id="r", ticker="NVDA", scorer="lexicon", score=0.5)
    seed_reading(graph, run_id="r", ticker="NVDA", scorer="provider", score=0.5)
    # both readings present but finbert under a different model:
    seed_reading(graph, run_id="r", ticker="META", scorer="lexicon", score=0.5)
    seed_reading(graph, run_id="r", ticker="META", scorer="provider", score=0.5)
    seed_finbert(graph, model_id="other-model", ref="r:META", value=0.5)
    returns = {
        "r:AAPL": 0.01,
        "r:MSFT": 0.02,
        "r:NVDA": 0.03,
        "r:META": 0.04,
        "r:MISSING": 0.05,  # no nodes at all
    }

    card = Scorecard.model_validate(
        bus.request(sentiment_scorecard_message(MODEL, returns)).payload
    )

    assert card.sample_size == 1  # only AAPL has all three legs under MODEL
    assert card.promotion_eligible is False


def test_no_forward_returns_yields_an_empty_scorecard() -> None:
    bus, graph, _sink = wire_forecaster(news={})
    _seed_complete(graph, "r", "AAPL", 0.8, 0.7, 0.9)

    card = Scorecard.model_validate(
        bus.request(sentiment_scorecard_message(MODEL, {})).payload
    )

    assert card.sample_size == 0
    assert card.metrics == {}
    assert card.promotion_eligible is False
