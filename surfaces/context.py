"""Surface wiring helpers.

Agent: surfaces
Role: build shared graph and bus contexts for CLI and tests.
External I/O: optional PostgreSQL graph construction in paper_context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from agents.execution.broker import PaperBroker
from agents.operator import OperatorAgent
from agents.provider.sources import FakeDataSource
from agents.scanner.universe import FakeUniverse
from kernel import (
    CollectingFaultSink,
    FakeLLMClient,
    InMemoryGraphStore,
    InProcessBus,
    MarketPackRegistry,
    MeteredFaultSink,
    NullMetrics,
)
from kernel.graph_env import build_graph_from_env
from orchestration.bindings import bind_paper_loop_agents
from orchestration.packs import USEquitiesSP500Pack
from orchestration.settings import OrchestratorSettings

if TYPE_CHECKING:
    from agents.execution.broker import Broker
    from agents.provider.sources import DataSource
    from agents.scanner.universe import UniverseSource
    from kernel import FaultSink, GraphStore, LLMClient, MessageBus, Metrics


@dataclass(frozen=True)
class SurfaceContext:
    """Shared dependencies for operator-facing surfaces."""

    graph: GraphStore
    bus: MessageBus
    pack_registry: MarketPackRegistry = field(default_factory=MarketPackRegistry)


def paper_context(
    source: DataSource | None = None,
    broker: Broker | None = None,
    graph: GraphStore | None = None,
    llm: LLMClient | None = None,
    pack_registry: MarketPackRegistry | None = None,
    metrics: Metrics | None = None,
) -> SurfaceContext:
    """Build a production-ready context with graph, bus, and all agents bound."""
    active_graph = graph if graph is not None else build_graph_from_env()
    return _context(
        active_graph,
        source=source,
        broker=broker,
        universe_source=None,
        llm=llm,
        pack_registry=pack_registry,
        metrics=metrics,
    )


def build_test_context(
    graph: GraphStore | None = None,
    source: DataSource | None = None,
    broker: Broker | None = None,
    llm: LLMClient | None = None,
    pack_registry: MarketPackRegistry | None = None,
) -> SurfaceContext:
    """Build an infra-free context with in-memory graph, bus, and all agents bound."""
    active_graph = graph if graph is not None else InMemoryGraphStore()
    return _context(
        active_graph,
        source=source or FakeDataSource(),
        broker=broker or PaperBroker(),
        universe_source=FakeUniverse({"sp500": ("AAPL",)}),
        llm=llm or FakeLLMClient({}),
        pack_registry=pack_registry,
    )


test_context = build_test_context


def _context(
    graph: GraphStore,
    *,
    source: DataSource | None,
    broker: Broker | None,
    universe_source: UniverseSource | None,
    llm: LLMClient | None,
    pack_registry: MarketPackRegistry | None,
    metrics: Metrics | None = None,
) -> SurfaceContext:
    sink = CollectingFaultSink()
    active_sink: FaultSink = MeteredFaultSink(metrics, sink) if metrics else sink
    bus = InProcessBus(sink=active_sink, metrics=metrics or NullMetrics())
    _bind_pipeline(bus, graph, source, broker, universe_source, active_sink)
    OperatorAgent(bus, graph=graph, llm=llm, sink=active_sink).bind()
    return SurfaceContext(
        graph=graph,
        bus=bus,
        pack_registry=pack_registry or _default_pack_registry(),
    )


def _bind_pipeline(
    bus: InProcessBus,
    graph: GraphStore,
    source: DataSource | None,
    broker: Broker | None,
    universe_source: UniverseSource | None,
    sink: FaultSink,
) -> None:
    bind_paper_loop_agents(
        bus,
        graph=graph,
        settings=OrchestratorSettings(),
        source=source,
        broker=broker,
        universe_source=universe_source,
        sink=sink,
    )


def _default_pack_registry() -> MarketPackRegistry:
    registry = MarketPackRegistry()
    registry.register(USEquitiesSP500Pack())
    return registry
