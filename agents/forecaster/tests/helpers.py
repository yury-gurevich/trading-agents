"""Forecaster test helpers.

Agent: forecaster
Role: provide deterministic provider+forecaster wiring and message builders.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agents.forecaster import ForecasterAgent
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.forecaster import ForecastRequest, ScorecardRequest
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from agents.forecaster.model import SentimentModel
    from agents.forecaster.settings import ForecasterSettings


def wire_forecaster(
    *,
    news: dict[str, tuple[str, ...]] | None = None,
    model: SentimentModel | None = None,
    settings: ForecasterSettings | None = None,
    register_provider: bool = True,
    fail_news: bool = False,
) -> tuple[InProcessBus, InMemoryGraphStore, CollectingFaultSink]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    if register_provider:
        ProviderAgent(
            bus,
            graph=graph,
            source=FakeDataSource(news=news, fail_news=fail_news),
            settings=ProviderSettings(max_staleness_days=7),
        ).bind()
    ForecasterAgent(bus, graph=graph, model=model, settings=settings, sink=sink).bind()
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
