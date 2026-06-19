"""Forecaster test helpers.

Agent: forecaster
Role: provide deterministic provider+forecaster wiring and message builders.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

from agents.forecaster import ForecasterAgent
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.forecaster import (
    ForecastRequest,
    ScorecardRequest,
    SentimentScorecardRequest,
)
from contracts.provider import OHLCVBar
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from agents.forecaster.model import SentimentModel
    from agents.forecaster.return_model import ReturnModel
    from agents.forecaster.settings import ForecasterSettings


def wire_forecaster(
    *,
    news: dict[str, tuple[str, ...]] | None = None,
    bars: tuple[OHLCVBar, ...] = (),
    model: SentimentModel | None = None,
    return_model: ReturnModel | None = None,
    settings: ForecasterSettings | None = None,
    register_provider: bool = True,
    fail_news: bool = False,
    fail_ohlcv: bool = False,
) -> tuple[InProcessBus, InMemoryGraphStore, CollectingFaultSink]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    if register_provider:
        ProviderAgent(
            bus,
            graph=graph,
            source=FakeDataSource(
                bars=bars, news=news, fail_news=fail_news, fail_ohlcv=fail_ohlcv
            ),
            settings=ProviderSettings(max_staleness_days=7),
        ).bind()
    ForecasterAgent(
        bus,
        graph=graph,
        model=model,
        return_model=return_model,
        settings=settings,
        sink=sink,
    ).bind()
    return bus, graph, sink


def forecast_message(
    subject_ref: str,
    *,
    subject_kind: Literal["recommendation", "position"] = "recommendation",
    features: dict[str, float] | None = None,
) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="forecaster",
        message_type="request",
        capability="forecast",
        payload=ForecastRequest(
            subject_kind=subject_kind,
            subject_ref=subject_ref,
            features=features or {},
        ).model_dump(mode="json"),
    )


def scorecard_message(model_id: str) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="forecaster",
        message_type="request",
        capability="scorecard",
        payload=ScorecardRequest(model_id=model_id).model_dump(mode="json"),
    )


def sentiment_scorecard_message(
    model_id: str, forward_returns: dict[str, float]
) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="forecaster",
        message_type="request",
        capability="sentiment_scorecard",
        payload=SentimentScorecardRequest(
            model_id=model_id, forward_returns=forward_returns
        ).model_dump(mode="json"),
    )


def seed_reading(
    graph: InMemoryGraphStore,
    *,
    run_id: str,
    ticker: str,
    scorer: str,
    score: float,
) -> None:
    """Write a SentimentReading node as the analyst would (for alignment tests)."""
    graph.merge_node(
        "SentimentReading",
        f"{run_id}:{scorer}:{ticker}",
        {
            "ticker": ticker,
            "scorer": scorer,
            "score": score,
            "articles": 0.0,
            "positive": 0.0,
            "negative": 0.0,
            "source_run_id": run_id,
        },
    )


def seed_finbert(
    graph: InMemoryGraphStore,
    *,
    model_id: str,
    ref: str,
    value: float,
    run: str = "fc",
) -> None:
    """Write a finbert ShadowPrediction node keyed by its subject ref."""
    graph.merge_node(
        "ShadowPrediction",
        f"{model_id}:{ref}:{run}",
        {
            "subject_ref": ref,
            "model_id": model_id,
            "value": value,
            "confidence": 1.0,
            "shadow": True,
            "source_run_id": run,
        },
    )


def make_bars(
    ticker: str, closes: tuple[float, ...], *, volume: int = 1000
) -> tuple[OHLCVBar, ...]:
    """Build a ticker's recent daily bars ending today (inside the fetch window)."""
    end = datetime.now(tz=UTC).date()
    count = len(closes)
    return tuple(
        OHLCVBar(
            ticker=ticker,
            bar_date=end - timedelta(days=count - 1 - index),
            open=close,
            high=close,
            low=close,
            close=close,
            volume=volume,
        )
        for index, close in enumerate(closes)
    )
