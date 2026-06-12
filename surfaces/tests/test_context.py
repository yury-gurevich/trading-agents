"""Surface context tests.

Agent: surfaces
Role: verify paper and test contexts bind the operator-facing bus.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker import PaperBroker
from agents.provider.sources import FakeDataSource
from kernel import (
    AgentMessage,
    FakeLLMClient,
    InMemoryGraphStore,
    MarketPackRegistry,
    PrometheusMetrics,
)
from surfaces.context import paper_context
from surfaces.context import test_context as build_context

if TYPE_CHECKING:
    import pytest


def test_test_context_binds_operator_and_supervisor() -> None:
    ctx = build_context()
    status = ctx.bus.request(
        AgentMessage(
            sender="test",
            recipient="supervisor",
            message_type="request",
            capability="system_status",
            payload={},
        )
    )
    command = ctx.bus.request(
        AgentMessage(
            sender="test",
            recipient="operator",
            message_type="request",
            capability="interpret",
            payload={"text": "status", "actor": "tester", "channel": "dashboard"},
        )
    )
    assert status.payload["healthy"] is True
    assert command.payload["outcome"] == "intent"
    assert ctx.pack_registry.get("us_equities_sp500") is not None


def test_context_accepts_custom_pack_registry() -> None:
    registry = MarketPackRegistry()
    ctx = build_context(pack_registry=registry)

    assert ctx.pack_registry is registry
    assert ctx.pack_registry.get("us_equities_sp500") is None


def test_paper_context_accepts_injected_graph() -> None:
    graph = InMemoryGraphStore()
    ctx = paper_context(
        source=FakeDataSource(),
        broker=PaperBroker(),
        graph=graph,
        llm=FakeLLMClient({}),
    )
    assert ctx.graph is graph


def test_paper_context_passes_metrics_to_bus() -> None:
    metrics = PrometheusMetrics()
    graph = InMemoryGraphStore()
    ctx = paper_context(
        source=FakeDataSource(),
        broker=PaperBroker(),
        graph=graph,
        llm=FakeLLMClient({}),
        metrics=metrics,
    )
    # Drive one bus request so the metered bus records it
    ctx.bus.request(
        AgentMessage(
            sender="test",
            recipient="supervisor",
            message_type="request",
            capability="system_status",
            payload={},
        )
    )
    text = metrics.exposition().decode("utf-8")
    assert "trading_agents_kernel_requests_total" in text


def test_paper_context_builds_default_graph_without_real_neo4j(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = InMemoryGraphStore()
    monkeypatch.setattr("surfaces.context.Neo4jGraphStore", lambda: graph)
    ctx = paper_context(
        source=FakeDataSource(),
        broker=PaperBroker(),
        llm=FakeLLMClient({}),
    )
    assert ctx.graph is graph
